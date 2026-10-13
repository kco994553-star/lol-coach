"""Authenticated private pro-cache envelope; public artifacts contain ciphertext only.

The runner derives a domain-specific key from an existing long-lived Secret.
That Secret never leaves its environment. Rotation/decryption failure blocks
collection instead of rebuilding stable identities or overwriting history.
"""
import io
import os
import re
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile

MAGIC=b'LCPRO1\0'
AAD=b'kco994553-star/lol-coach:private-pro-reference-cache:v1'
MAX_BYTES=512_000_000
MAX_FILE_BYTES=20_000_000
MAX_FILES=2000


def _member_allowed(name):
    return name in {'accounts.json','collection-receipt.json','reference-data.json','reference-cases.json','private/','private/matches/'} or re.fullmatch(r'private/matches/[a-f0-9]{64}\.json',name) is not None


def _key(seed):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    if not isinstance(seed,str) or not seed:raise ValueError('PRIVATE_CACHE_KEY_REQUIRED')
    return HKDF(algorithm=hashes.SHA256(),length=32,salt=AAD,
                info=b'lol-coach/pro-reference-cache/v1').derive(seed.encode())


def _path(path):
    p=Path(path)
    if '..' in p.parts or any(x.is_symlink() for x in (p,*p.parents)):
        raise ValueError('PRIVATE_CACHE_UNSAFE_PATH')
    return p


def encrypt_directory(directory,output,seed):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    root=_path(directory);out=_path(output);key=_key(seed)
    if not root.is_dir():raise ValueError('PRIVATE_CACHE_DIRECTORY_REQUIRED')
    content=io.BytesIO();total=0;files=0
    with zipfile.ZipFile(content,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(root.rglob('*')):
            _path(p)
            if p.is_dir():continue
            if not p.is_file():raise ValueError('PRIVATE_CACHE_NOT_REGULAR_FILE')
            if not _member_allowed(p.relative_to(root).as_posix()):raise ValueError('PRIVATE_CACHE_UNEXPECTED_MEMBER')
            size=p.stat().st_size;total+=size;files+=1
            if size>MAX_FILE_BYTES or total>MAX_BYTES or files>MAX_FILES:
                raise ValueError('PRIVATE_CACHE_SIZE_LIMIT')
            archive.writestr(p.relative_to(root).as_posix(),p.read_bytes())
    if content.tell()>MAX_BYTES:raise ValueError('PRIVATE_CACHE_SIZE_LIMIT')
    nonce=os.urandom(12);envelope=MAGIC+nonce+AESGCM(key).encrypt(nonce,content.getvalue(),AAD)
    out.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.pro-cache-',dir=out.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(envelope);stream.flush();os.fsync(stream.fileno())
        os.replace(name,out)
    finally:
        if os.path.exists(name):os.unlink(name)
    return {'status':'ENCRYPTED','files':files,'privacy':'AUTHENTICATED_CIPHERTEXT_ONLY'}


def decrypt_directory(bundle,directory,seed):
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    source=_path(bundle);target=_path(directory);key=_key(seed)
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError('PRIVATE_CACHE_DESTINATION_NOT_EMPTY')
    if not source.is_file() or source.stat().st_size>MAX_BYTES+100:
        raise ValueError('PRIVATE_CACHE_INVALID_ENVELOPE')
    body=source.read_bytes()
    if not body.startswith(MAGIC) or len(body)<len(MAGIC)+28:
        raise ValueError('PRIVATE_CACHE_INVALID_ENVELOPE')
    start=len(MAGIC)
    try:plain=AESGCM(key).decrypt(body[start:start+12],body[start+12:],AAD)
    except InvalidTag:raise ValueError('PRIVATE_CACHE_AUTHENTICATION_FAILED') from None
    try:
        with zipfile.ZipFile(io.BytesIO(plain)) as archive:
            members=archive.infolist();total=0;names=set()
            if len(members)>MAX_FILES:raise ValueError('PRIVATE_CACHE_SIZE_LIMIT')
            for member in members:
                p=PurePosixPath(member.filename);mode=member.external_attr>>16
                if not member.filename or '\\' in member.filename or p.is_absolute() or '..' in p.parts or ':' in member.filename or stat.S_ISLNK(mode) or member.filename in names or not _member_allowed(member.filename):
                    raise ValueError('PRIVATE_CACHE_UNSAFE_MEMBER')
                names.add(member.filename);total+=member.file_size
                if member.file_size>MAX_FILE_BYTES or total>MAX_BYTES:
                    raise ValueError('PRIVATE_CACHE_SIZE_LIMIT')
            # Validate every member before creating any plaintext.
            target.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(target,0o700)
            for member in members:
                dest=target/member.filename
                if member.is_dir():dest.mkdir(parents=True,exist_ok=True,mode=0o700);continue
                dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
                fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'wb') as stream:stream.write(archive.read(member))
    except (zipfile.BadZipFile,RuntimeError):raise ValueError('PRIVATE_CACHE_INVALID_ARCHIVE') from None
    return {'status':'RESTORED','files':len(members),'privacy':'RUNNER_EPHEMERAL_PRIVATE'}
