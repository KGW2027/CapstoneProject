1. 절대 main-branch에 commit, push를 하지마세요.
 - main branch는 목표가 일정 waystone에 도달할 때, 'app-' branch에서 PR로 merge됩니다.

2. crawler와 관련된 업데이트 사항은 app-crawler, 
  DL model과 관련된 업데이트 사항은 app-model이 메인 브랜치입니다.

3. 기능 추가를 위해서는 'app-' branch를 base로 새로운 브랜치 'feature-(기능 이름)'을 만든 뒤 진행해주세요.
 - 이후, 기능을 완성했다면 버그에 대해 테스트 하시고 base로 했던 branch에 PR을 넣어주세요.
 - PR에 대해서는 다같이 검증 후 merge를 진행합니다.

4. 'app-' branch에 원래 있던 클래스에 변경을 가하지 마세요.
 - 만약, 'feature-' branch에서 특정 기능이 필요하거나 버그가 있어 'app-' branch에 수정이 필요하다면
   'app-' branch를 base로 하는 'hotfix-' branch를 만들어서 수정 후 PR을 넣어주세요.
 - 이후, hotfix가 app에 병합되면, 
   기존 변경점을 Stash한 뒤에 rebase 혹은 pull로 불러온 뒤, 다시 기존 변경점을 덮어씌우면 됩니다. 

5. branch 구조는 다음과 같습니다.
 1: 업데이트 시기 : Waystone에 도달, 제출
 ※ 절대 임의로 Merge를 하지마세요. 반드시 Pull Request를 요청하세요.
  [main]

 2: 업데이트 시기 : feature 완성 후, hotfix 
 ※ 절대 임의로 Merge를 하지마세요. 반드시 Pull Request를 요청하세요.
    [app-model] 
    [app-crawler]

 3-1: 각자 기능 추가를 위해 app-을 기반으로 새로운 branch를 판 뒤 알아서 커밋/푸시
    [feature-'name']

 3-2: app-에 존재하는 클래스에 대한 긴급한 버그 혹은 기능 추가에 대해 커밋/푸시
    [hotfix-'name']

    