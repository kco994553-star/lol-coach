/* Authored conditional tactics. Edit data and bump version; no approval implied. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory();
  else root.LoadingDirectionProfiles=factory();
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  return {
  "schema_version": "gameplan-direction-profiles-v1",
  "version": "2",
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
    },
    "Fiora": {
      "role": "TOP",
      "required_slots": [
        "P",
        "Q",
        "W",
        "R"
      ],
      "provenance": {
        "source_path": "web_r4/loading-planboard.js",
        "locator": "enrichCoaching:if(fiora)",
        "basis": "EXISTING_AUTHORED_PROSE_MIGRATION_NOT_VALIDATION"
      },
      "phases": {
        "lane": {
          "keys": [
            "P",
            "Q",
            "W"
          ],
          "gain": "접근하기 쉬운 급소를 치고 빠지는 교환부터 비교한다.",
          "method": "적 미니언이 많거나 급소가 뒤에 있으면 무리하게 돌아가지 않는다.",
          "explanation": "접근하기 쉬운 급소를 치고 빠지는 교환부터 비교한다. 적 미니언이 많거나 급소가 뒤에 있으면 무리하게 돌아가지 않는다. {W}는 단독 교환과 정글 개입 상황에서 남길 가치가 다르다. 가까운 거리의 진입을 매번 반응해서 막는 것을 기본 계획으로 삼지 않는다."
        },
        "operations": {
          "keys": [
            "Q",
            "W"
          ],
          "gain": "상대 한 명을 사이드에 묶고 미니언·포탑 이득을 쌓는다.",
          "method": "사이드 압박 시간을 중앙과 맞추기",
          "explanation": "사이드는 깊이보다 타이밍이 중요하다. 중앙 아군이 미니언을 밀거나 견제하는 순간에 포탑을 위협해야 상대의 대응을 나눌 수 있다. 상대가 나를 두고 중앙으로 떠나면 바로 위험을 알린다. 포탑을 더 때릴지 합류할지는 얻을 포탑과 아군 손실, 이동 시간·순간이동을 비교해 정한다."
        },
        "fight": {
          "keys": [
            "P",
            "W",
            "R"
          ],
          "gain": "사이드로 상대를 나누고 교전에서는 함께 닿는 적을 공격하는 역할",
          "method": "진입을 받아치거나, 고립된 적에게 접근하기",
          "explanation": "{R}는 적 원딜에게만 쓰지 않는다. 아군과 함께 잡을 수 있는 진입자에게 사용해 회복 구역을 만들 기회도 본다. 회복은 네 급소를 모두 치거나 급소를 하나 이상 친 대상이 죽어야 생긴다. 단순히 궁을 썼다고 아군이 보호받는 것은 아니다."
        }
      }
    },
    "Graves": {
      "role": "JUNGLE",
      "required_slots": [
        "P",
        "Q",
        "W",
        "E"
      ],
      "provenance": {
        "source_path": "web_r4/loading-planboard.js",
        "locator": "enrichCoaching:if(graves)",
        "basis": "EXISTING_AUTHORED_PROSE_MIGRATION_NOT_VALIDATION"
      },
      "phases": {
        "lane": {
          "keys": [
            "P",
            "Q",
            "E"
          ],
          "gain": "캠프 성장을 유지하면서 상대 정글의 개입이 큰 손해로 이어지지 않게 돕는다.",
          "method": "아군이 먼저 움직일 수 있는 라인 쪽에서 캠프와 지원을 연결한다. 탑 챔피언만 보고 시작 동선을 고정하지 않는다.",
          "explanation": "개입은 도착 후 실제로 적에게 닿을 수 있는지부터 판단한다. 아군의 제어·체력·웨이브가 맞지 않으면 기다리는 시간만 늘어 성장도 늦어진다. 상대 정글이 반대편에 보여도 목표물 확보가 자동으로 안전해지는 것은 아니다. 가까운 라인이 먼저 움직일 수 있는지와 처리할 체력·시간을 확인한다."
        },
        "operations": {
          "keys": [
            "P",
            "Q",
            "E"
          ],
          "gain": "캠프 성장과 아군 지원을 포탑·시야·목표물 이득으로 연결한다.",
          "method": "성장 동선과 라인 지원을 연결하기",
          "explanation": "아군이 먼저 움직일 수 있을 때 상대 정글과 강을 압박한다. 라인 지원이 없으면 내 캠프와 역갱 기회로 성장한다. 아군이 귀환 중이거나 중앙에서 밀리고 있다면 깊은 침입을 줄인다. 중앙과 사이드가 동시에 압박할 때 상대가 대응하기 어려워진다."
        },
        "fight": {
          "keys": [
            "P",
            "W",
            "E"
          ],
          "gain": "성장한 화력을 아군과 연결하고 후속 공격을 방해하는 정글러",
          "method": "진입을 피하고, 아군과 가까운 적부터 공격하기",
          "explanation": "{W}는 접근 가능한 적 후속 딜러의 시야를 방해하는 데 쓴다. 연막을 맞히려고 혼자 깊이 들어가거나, 연막 하나로 궁극기 연계가 차단된다고 기대하지 않는다. 첫 진입을 버틴 뒤 아군과 함께 공격할 틈을 찾는다. 장전 중에도 무리하게 적에게 붙어 있지 말고 퇴로와 다음 공격 위치를 확보한다."
        }
      }
    }
  }
};
});
