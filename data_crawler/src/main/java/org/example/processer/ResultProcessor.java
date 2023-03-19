package org.example.processer;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.*;
import java.util.HashSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ResultProcessor {

    public static void main(String[] args) throws IOException, ParseException {
//        new ResultProcessor("./data/FandomEnTranslated/Fandom-EnKo-DeepL.json")
//                .process();
        new ResultProcessor("./data/UniverseEnTranslated/Univ-Enko-DeepL.json")
                .process();
    }


    private JSONArray array;
    private File output;
    private JSONObject properMap;
    private int engc;

    private ResultProcessor(String path) throws IOException, ParseException {

        File properFile = new File("./data/propermap.json");
        BufferedReader propReader = new BufferedReader(new InputStreamReader(new FileInputStream(properFile)));
        String line;
        StringBuilder builder = new StringBuilder();
        while ((line = propReader.readLine()) != null) builder.append(line);
        properMap = (JSONObject) new JSONParser().parse(builder.toString());

        File file = new File(path);
        BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(file)));
        builder.setLength(0);

        while ((line = reader.readLine()) != null) builder.append(line);
        array = (JSONArray) new JSONParser().parse(builder.toString());

        output = new File(path.replace(".json", "-process.json"));
        if (!output.exists()) output.createNewFile();
    }

    private void process() {
        HashSet<String> processed = new HashSet<>();
engc =0;
        for (Object o : array) {
            String sentence = (String) o;
            if((sentence = postProcess(sentence)) != null) processed.add(sentence);
        }

        JSONArray jsonArray = new JSONArray();
        for (String text : processed) jsonArray.add(text);

        System.out.println(engc);

        try {
            BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(output)));
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            JsonElement ge = JsonParser.parseString(jsonArray.toJSONString());
            writer.write(gson.toJson(ge));
            writer.flush();
            writer.close();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private String postProcess(String text) {
        Pattern english = Pattern.compile("[a-zA-Z]+");
        Pattern years = Pattern.compile("20[0-9]{2}");
        Pattern numStart = Pattern.compile("^[0-9]");
        Pattern gameInfo = Pattern.compile("([0-9]\\.[0-9]*)|(공격력|방어력|게임 모드|미니언|플레이|패치|유닛|주문 피해|물리 피해|기본 생명력|군중 제어|경험치|획득량|재사용 대기|체력|매개변수|템플릿|시야 반경|면역|활성화|증가|감소|적 챔피언|아군 챔피언)");

        // 연도 정보가 포함되어 있으면 이벤트 정보일 확률이 높음.
        if(years.matcher(text).find()) return null;

        // 숫자로 시작하는 경우 이상한 정보일 경우가 많음.
        if(numStart.matcher(text).find()) return null;
        
        // 콜론이 들어가 있으면 스킬 설명, 잡다한 정보일 확률이 대략 80%정도 됨. (20%의 오차를 없애는 현명한 방법을 찾지 못함)
        int colonIdx = text.indexOf(":");
        if (colonIdx >= 0) return null;

        // 패치가 들어있으면 게임 패치와 관련된 내용일 가능성이 높음 ( 45개중 대략 10개정도는 일반 텍스트 )
        // 게임 내 정보일 확률이 높은 키워드는 위의 gameInfo Pattern에 추가
        Matcher matcher = gameInfo.matcher(text);
        if(matcher.find()) return null;

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
                .replace("엘리즈", "엘리스")
                .replace("아이버", "아이번")
                .replace("모르데카이저", "모데카이저")
                .replace("베이가르", "베이가")
                .replace("워릭", "워윅")
                .replace("발리베어", "볼리베어")
                .replace("말자하르", "말자하")
                .replace("스카르너", "스카너")
                .replace("신자오", "신짜오")
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
                .replace("&", "와 ")
                .replaceAll("잭(?!스)", "자크")
                .replaceAll("(?<!아)이오니아", "아이오니아")
                .replaceAll("(?<!아)이오니안", "아이오니안")
                .replaceAll("(?<!인)빅터(?!터스)", "빅토르")
                .replaceAll("['\",`=><]", "")
                .replaceAll("\\.{2,}", ".")
                .replaceAll(" {2,}", " ")
                .replaceAll("-{2,}", "-")
                ;

        // 이후 영어가 남아있는 경우 보통 의미 없는 문장인 경우가 많음.
        if(english.matcher(text).find()) {
            ++engc;
            return null;
        }

        // 길이가 너무 짧은 문장 혹은 띄어쓰기가 적은 문장은 무의미할 가능성이 높음.
        if(text.length() < 6 || text.split(" ").length <= 3) return null;

        // -로 시작하는 문장은 앞의 -를 제거
        if(text.startsWith("-")) text = text.replace("-", "");

        // 불필요한 공백 제거
        return text.trim();
    }
}
