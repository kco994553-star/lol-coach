/* Authored conditional tactics. Edit data and bump version; no approval implied. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory();
  else root.LoadingDirectionProfiles=factory();
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  return {
  "schema_version": "gameplan-direction-profiles-v1",
  "version": "1",
  "source_patch": "16.20.1",
  "review_state": "TACTICAL_UNREVIEWED",
  "champions": {
    "Caitlyn": {
      "role": "BOTTOM",
      "required_slots": [
        "P",
        "Q",
        "W",
        "E"
      ],
      "phases": {
        "lane": {
          "keys": [
            "Q",
            "W",
            "P"
          ],
          "gain": "막타 접근을 방해할 공간과 웨이브 압박",
          "method": "기본 공격과 관통 사격으로 압박하고, 이동이 제한된 적에게 배운 덫을 연결",
          "explanation": "케이틀린은 기본 공격과 {Q}로 상대의 막타 접근을 방해하고, 그 공간을 웨이브 압박으로 잇는 방향을 먼저 검토한다. 배운 {W}를 이동이 제한된 적에게 연결할 수도 있지만, 상대 두 명의 반격을 받으며 밀어야 한다면 이 압박부터 강제하지 않는다."
        },
        "operations": {
          "keys": [
            "Q",
            "W"
          ],
          "gain": "포탑에 접근할 시간과 상대의 중앙 수비 유도",
          "method": "밀어 넣은 웨이브와 배운 덫으로 접근 공간을 만들고 포탑 압박과 이동을 비교",
          "explanation": "케이틀린은 밀어 넣은 웨이브를 포탑 압박으로 이어 상대가 수비하러 오게 만드는 방향을 검토한다. 배운 {W}로 접근 경로를 제한할 수 있어도 안전한 철거가 보장되지는 않는다. 실제로 미드를 지키는 적의 정리 속도와 측면 위협을 확인해, 압박을 유지할지 상대가 받는 동안 이동할지 나눈다."
        },
        "fight": {
          "keys": [
            "W",
            "E",
            "P"
          ],
          "gain": "아군과 거리를 유지하면서 반복해서 공격할 시간",
          "method": "기본 공격을 이어가며 배운 덫·투망과 강화 공격을 활용",
          "explanation": "케이틀린은 아군이 도울 수 있는 거리에서 기본 공격을 이어가고, 배운 {W}나 {E}가 맞으면 강화된 {P}를 활용하는 방향을 잡는다. 덫 연계를 위해 앞으로 걸어가는 동안 상대가 나에게 접근할 수 있다면, 추가 공격보다 퇴로와 다음 공격 위치를 먼저 남긴다."
        }
      }
    },
    "Ezreal": {
      "role": "BOTTOM",
      "required_slots": [
        "P",
        "Q",
        "W",
        "E"
      ],
      "phases": {
        "lane": {
          "keys": [
            "Q",
            "P"
          ],
          "gain": "체력과 막타 접근을 유지하며 다음 공격 기회 확보",
          "method": "화살 적중과 가능한 거리의 기본 공격을 함께 사용",
          "explanation": "이즈리얼은 {Q}로 닿는 적을 견제하면서 막타 접근을 유지하고, 함께 공격할 수 있는 거리에서는 기본 공격도 보태는 방향을 잡는다. 스킬 적중으로 {P}의 공격 속도를 얻을 수 있지만, 화살이 미니언에 막히는 자리와 상대 두 명이 함께 공격하는 자리를 같은 교환 기회로 보지 않는다."
        },
        "operations": {
          "keys": [
            "Q",
            "W",
            "E"
          ],
          "gain": "안전한 합류와 견제로 얻는 포탑·목표물 접근 시간",
          "method": "동료와 공격 경로를 확보해 견제하고, 접근 가능한 목표에 배운 스킬을 활용",
          "explanation": "이즈리얼은 아군과 {Q}가 닿을 경로를 만들고, 상대가 물러난 시간에 포탑이나 목표물에 접근하는 방향을 검토한다. 배운 {W}를 목표물에 활용할 수 있어도 웨이브를 먼저 밀 수 있다는 뜻은 아니다. 실제 중앙 수비 인원과 합류 거리를 확인하고, {E}를 배웠다는 이유만으로 혼자 어두운 길을 통과하지 않는다."
        },
        "fight": {
          "keys": [
            "Q",
            "P",
            "E"
          ],
          "gain": "공격 거리를 다시 잡으며 지속해서 피해를 줄 시간",
          "method": "화살과 기본 공격을 함께 쓰고 배운 이동기로 공격 위치를 조정",
          "explanation": "이즈리얼은 {Q}와 기본 공격을 이어가며, 배운 {E}로 공격 위치를 조정하는 방향을 잡는다. 이동기를 앞으로 쓰면 다음 접근을 피할 수단이 줄어드므로, 아군이 적을 묶어도 도착할 자리에서 공격을 이어가고 빠져나올 수 있는지부터 확인한다."
        }
      }
    }
  }
};
});
