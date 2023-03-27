package org.example.translator;

import org.example.ChromeDriver;
import org.openqa.selenium.By;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

enum TranslatorAPIs {
    GOOGLE("https://translate.google.co.kr/?sl={START}&tl={END}&text={TEXT}&op=translate", By.className("ryNqvb"), ExpectedConditions.presenceOfElementLocated(By.className("ryNqvb")), 5000),
    DEEPL("https://www.deepl.com/translator#{START}/{END}/{TEXT}",
            By.cssSelector("#panelTranslateText > div.lmt__sides_container > div.lmt__sides_wrapper > section.lmt__side_container.lmt__side_container--target > div.lmt__textarea_container > div.lmt__inner_textarea_container > d-textarea > div"),
            ChromeDriver.attributeToBeNotEmpty(By.cssSelector("#panelTranslateText > div.lmt__sides_container > div.lmt__sides_wrapper > section.lmt__side_container.lmt__side_container--target > div.lmt__textarea_container > div.lmt__inner_textarea_container"), "title"),
            3000)
    ;

    String baseURL;
    By waitElement;
    ExpectedCondition waitCondition;
    int maxLength;

    static String FROM = "{START}";
    static String TO = "{END}";
    static String TEXT = "{TEXT}";

    TranslatorAPIs(String url, By element, ExpectedCondition waitCondition, int maxLength) {
        baseURL = url;
        waitElement = element;
        this.waitCondition = waitCondition;
        this.maxLength = (int) (maxLength * 0.9);
    }
}

public class TranslatorMachine {

    /*
     * 1. Builder에 Text를 입력받음.
     * 2. Text의 길이가 제한을 넘어가면 강제로 apply하고 결과를 return
     */

    private ChromeDriver driver;
    private StringBuilder builder;
    private int maxLength;
    private By resultElement;
    private String url;

    public TranslatorMachine(TranslatorAPIs api) {

        driver = new ChromeDriver()
                .setTimeout(10L)
                .setWait(api.waitCondition)
                .setVpnUsable(api == TranslatorAPIs.DEEPL)
//                .enableHeadlessMode()
                .init()
        ;

        builder = new StringBuilder();
        maxLength = Math.round(api.maxLength * 0.9f);
        url = api.baseURL;
        resultElement = api.waitElement;

    }

    public TranslatorMachine setLanguage(Language from, Language to) {
        url = url
                .replace(TranslatorAPIs.FROM, from.getLangKey())
                .replace(TranslatorAPIs.TO, to.getLangKey())
                ;
        return this;
    }

    private void append(String text) {
        builder.append(text).append("\n\n");
    }

    public List<String> appendText(String text) {
        List<String> result = null;
        text = preprocess(text);
        if(text.length() + builder.length() >= maxLength)
            result = flush();

        append(text);
        return result;
    }

    public List<String> flush() {
        if(builder.length() == 0) return null;
        if(builder.toString().replace("\n", "").equals("")) return null;

        String preprocString = builder.toString()
                .replace("/", " ")
                .replace("\n", "%0A");
        String connect = url.replace(TranslatorAPIs.TEXT, preprocString);
        builder.setLength(0);
        while(true) {
            try {
                driver.connect(connect);
                break;
            } catch (TimeoutException timeout) {
                driver.reconnect();
            }
        }

        List<WebElement> elements = driver.findElements(resultElement);
        List<String> splits = new ArrayList<>();
        for(WebElement element : elements)
            for(String split : element.getText().split("\n\n"))
                splits.add(postProcess(split));

        return splits;
    }

    private String preprocess(String line) {
        return line.replace("“", "\"")
                .replace("”", "\"")
                .replace("’", "'")
                .replace("‘", "'")
                .replace("…", "...")
                .replace("—", " ")
                .replace("–", "")
                .replace("ø", "o")
                .replace("♥", "love")
                .replace("á", "a")
                .replace("ä", "a")
                .replace("é", "e")
                .replace("í", "i")
                .replace("ö", "o")
                .replace("ü", "u")
                .replace("°", " degrees")
                .replace("·", ",")
                .replace("「", "\"")
                .replace("」", "\"")
                .replace("(bug)", "")
                .replace("(TBA)", "")
                .replaceAll("\\[.*?\\]", "")
                .replaceAll("\\(.*?\\)", "")
                .replaceAll("^([0-9]+\\n )", "")
                .replaceAll(" {2,}", " ")
                ;
    }

private String postProcess(String text) {
    Pattern english = Pattern.compile("[a-zA-Z]+");
    Pattern years = Pattern.compile("20[0-9]{2}");
    Pattern numStart = Pattern.compile("^[0-9]");
    Pattern gameInfo = Pattern.compile("( - )|(시즌 [0-9]+)|( [0-9]+ )|([0-9]\\.[0-9]*)|" +
            "(공격력|방어력|게임 모드|미니언|플레이|패치|유닛|주문 피해|물리 피해|기본 생명력|군중 제어|경험치|획득량|재사용 대기|체력|" +
            "매개변수|템플릿|시야 반경|면역|활성화|증가|감소|적 챔피언|아군 챔피언|컨셉 아트|일러스트|게임|모델|자세히 보기|지역 보기|관련 챔피언|스킨|크로마|스킬|리그 오브 레전드|기본 공격|주문 보호막|" +
            "궁극기|패시브|계산됩니다|중단되|아케인|애니메이션|이벤트)");


    // 연도 정보가 포함되어 있으면 이벤트 정보일 확률이 높음.
    if(years.matcher(text).find()) return null;

    // 숫자로 시작하는 경우 이상한 정보일 경우가 많음.
    if(numStart.matcher(text).find()) return null;

    // 콜론이 들어가 있으면 스킬 설명, 잡다한 정보일 확률이 대략 80%정도 됨. (20%의 오차를 없애는 현명한 방법을 찾지 못함)
    int colonIdx = text.indexOf(":");
    if (colonIdx >= 0) return null;

    // 주로 잘못입력된 정보를 교체함
    text = text.replace("T.F.", "트위스티드 페이트")
            .replace("티에프", "트위스티드 페이트")
            .replace("T.F", "트위스티드 페이트")
            .replace("CM", "cm")
            .replace("필토버", "필트오버")
            .replace("필오버", "필트오버")
            .replace("우르고트", "우르곳")
            .replace(" 다린", " 다르킨")
            .replace("다킨", "다르킨")
            .replace("헥스텍", "헥스테크")
            .replace("데마키안", "데마시안")
            .replace("자운인", "자우니트")
            .replace("자우나이트", "자우니트")
            .replace("프렐요르드", "프렐요드")
            .replace("프렐요르디안", "프렐요드인")
            .replace("타르곤", "타곤")
            .replace("타르고니아인", "타곤인")
            .replace("샤이바나", "쉬바나")
            .replace("질리안", "질리언")
            .replace("루루", "룰루")
            .replace("키야나", "키아나")
            .replace("에블린", "이블린")
            .replace("시온", "사이온")
            .replace("아니비아", "애니비아")
            .replace("강플랭크", "갱플랭크")
            .replace("엘리즈", "엘리스")
            .replace("아이버", "아이번")
            .replace("모르데카이저", "모데카이저")
            .replace("베이가르", "베이가")
            .replace("워릭", "워윅")
            .replace("발리베어", "볼리베어")
            .replace("말자하르", "말자하")
            .replace("스카르너", "스카너")
            .replace("신자오", "신짜오")
            .replace("신 자오", "신짜오")
            .replace("나수스", "나서스")
            .replace("익스탈", "이쉬탈")
            .replace("람무스", "람머스")
            .replace("신조", "신짜오")
            .replace("조냐의", "존야의")
            .replace("스와인", "스웨인")
            .replace("그레이브스", "그레이브즈")
            .replace("카시오페이아", "카시오페아")
            .replace("켄넨", "케넨")
            .replace("리 신", "리신")
            .replace("룩스", "럭스")
            .replace("모가나", "모르가나")
            .replace("포피", "뽀삐")
            .replace("파피", "뽀삐")
            .replace("양귀비", "뽀삐")
            .replace("지그스", "직스")
            .replace("실라스", "사일러스")
            .replace("악샨", "아크샨")
            .replace("싱드", "신지드")
            .replace("트위스티드 운명", "트위스티드 페이트")
            .replace("&", "와 ")
            .replaceAll("잭(?!스)", "자크")
            .replaceAll("그레이브(?!즈)", "그레이브즈")
            .replaceAll("(?<!아)이오니아", "아이오니아")
            .replaceAll("(?<!아)이오니안", "아이오니안")
            .replaceAll("(?<!인)빅터(?!터스)", "빅토르")
            .replaceAll("['\",`=><]", "")
            .replaceAll("\\.{2,}", ".")
            .replaceAll(" {2,}", " ")
            .replaceAll("-{2,}", "-")
            .replaceAll("(?=(\\(|\\[|\\{)).*?(?<=(\\)|\\]|\\}))", "")
            .replaceAll("[\\(\\[\\{\\}\\]\\)]", "")
    ;

    // 이후 영어가 남아있는 경우 보통 의미 없는 문장인 경우가 많음.
    if(english.matcher(text).find()) {
        return null;
    }

    // 길이가 너무 짧은 문장 혹은 띄어쓰기가 적은 문장은 무의미할 가능성이 높음.
    if(text.length() < 6 || text.split(" ").length <= 3) return null;

    // -로 시작하는 문장은 앞의 -를 제거
    if(text.startsWith("-")) text = text.replace("-", "");

    // ~가 들어가면서 그 뒤가 10글자 이내인 경우, 챔피언의 대사로 처리한다.
    if(text.contains("~")) {
        String[] split = text.split("~");
        if(split.length >= 2 && split[1].length() < 10) {
            text = split[0];
        }
    }

    // 패치가 들어있으면 게임 패치와 관련된 내용일 가능성이 높음 ( 45개중 대략 10개정도는 일반 텍스트 )
    // 게임 내 정보일 확률이 높은 키워드는 위의 gameInfo Pattern에 추가
    Matcher matcher = gameInfo.matcher(text);
    if(matcher.find()) return null;

    // 불필요한 공백 제거
    return text.trim();
}


}
