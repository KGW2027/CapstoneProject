package org.example.translator;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.example.ChromeDriver;
import org.example.processer.UniqueDict;
import org.example.translator.processors.FandomJSONParser;
import org.example.translator.processors.UniverseParser;
import org.json.simple.JSONArray;
import org.json.simple.parser.ParseException;
import org.openkoreantext.processor.OpenKoreanTextProcessorJava;
import org.openkoreantext.processor.tokenizer.Sentence;
import org.openqa.selenium.By;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.io.*;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

enum TranslatorAPI {
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

    TranslatorAPI(String url, By element, ExpectedCondition waitCondition, int maxLength) {
        baseURL = url;
        waitElement = element;
        this.waitCondition = waitCondition;
        this.maxLength = (int) (maxLength * 0.9);
    }

}

public class Translator {

    public static void main(String[] args) {
        new Translator(TranslatorAPI.DEEPL)
                .setStartLanguage(Language.ENGLISH)
                .setEndLanguage(Language.KOREAN)
                .initTexts(new FandomJSONParser())
//                .initTexts(new UniverseParser())
                .setAutosaveTerm(100)
                .translate()
        ;
    }

    private ChromeDriver driver;
    private String targetURL;
    private HashSet<String> texts;
    private File output;
    private int saveTerm;
    private TranslatorAPI api;
    private Long startTime;

    private Translator(TranslatorAPI api) {
        driver = new ChromeDriver()
                .setTimeout(10L)
                .setWait(api.waitCondition)
//                .enableHeadlessMode()
                .init()
                ;
        targetURL = api.baseURL;
        texts = new HashSet<>();
        saveTerm = -1;
        this.api = api;
    }

    public Translator setStartLanguage(Language lang) {
        targetURL = targetURL.replace("{START}", lang.getLangKey());
        return this;
    }

    public Translator setEndLanguage(Language lang) {
        targetURL = targetURL.replace("{END}", lang.getLangKey());
        return this;
    }

    public Translator setAutosaveTerm(int term) {
        saveTerm = term;
        return this;
    }

    public Translator initTexts(CrawlDataProcessor processor) {
        try {
            output = new File(String.format("./data/%s/translate_output.json", processor.getDirectoryName()));
            if (!output.getParentFile().exists()) output.getParentFile().mkdirs();
            if (!output.exists()) output.createNewFile();

            processor.process(texts);
        } catch (IOException | ParseException ex) {
            System.out.println("initTexts를 처리하던 중 오류가 발생했습니다.\n =====\t=====\t=====\t=====");
            ex.printStackTrace();
            System.out.println(" =====\t=====\t=====\t=====\"");
        }
        return this;
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
                .replaceAll("\\[.*?\\]", "")
                .replaceAll("\\(.*?\\)", "");
    }


    public void translate() {
        if (output == null) {
            throw new NullPointerException("번역 작업을 시작하기 전, initTexts를 먼저 진행해주세요.");
        }

        System.out.printf("%d개 문장을 발견하였습니다. 번역작업을 시작합니다.\n", texts.size());
        
        StringBuilder translate = new StringBuilder();
        List<String> requests = new ArrayList<>();
        Pattern exceptLiteral = Pattern.compile("[^\\u0000-\\u007E가-힣]"); // ascii 범위와 한글
        
        // 문장을 번역기에 보낼 텍스트로 가공
        for (String line : texts) {
            if (translate.length() + line.length() > api.maxLength) {
                requests.add(translate.toString());
                translate.setLength(0);
            }

            if(line.contains("rewards") || line.contains("pvp") || line.contains("point") || line.contains("level")) continue;

            line = preprocess(line);
            Matcher matcher = exceptLiteral.matcher(line);
            if(matcher.find()) continue;
            translate.append(line).append("\n\n");
        }
        if (translate.length() > 0) requests.add(translate.toString());

        // 출력 JSON
        JSONArray outputArray = new JSONArray();
        startTime = System.currentTimeMillis();
        String debugFormat = "[%d / %d (%.2f%%)] 예상 남은 시간 : %s :: %d 길이의 문자열에 대해 번역 요청";


        for (int idx = 0; idx < requests.size(); idx++) {
            String req = requests.get(idx);

            req = req.replace("/", " ");

            double progress = 100f * (idx + 1) / requests.size();
            System.out.printf(debugFormat, idx+1, requests.size(), progress, calcRemains(idx, requests.size()), req.length());

            String request = targetURL.replace("{TEXT}", req);
            try {
                driver.connect(request.replace("\n", "%0A"));
            } catch(TimeoutException timeout) {
                System.out.println(" :: TIMEOUT");
                if(api == TranslatorAPI.DEEPL) {
                    driver.reconnect();
                    idx -= 1;
                }
                continue;
            }

            List<WebElement> elements = driver.findElements(api.waitElement);
            dataProcess(elements, outputArray);

            if (saveTerm > 0 && (idx > 0 && idx % saveTerm == 0)) {
                save(outputArray);
            }
        }

        save(outputArray);
    }

    private String calcRemains(int did, int max) {
        long progress = System.currentTimeMillis() - startTime;
        double time = (((double) progress / did) * (max - did)) / 1000d;

        int hours = (int) Math.floor(time / 3600);
        time -= 3600 * hours;
        int mins = (int) Math.floor(time / 60);
        time -= 60 * mins;
        return String.format("%d시간 %02d분 %02d초", hours, mins, Math.round(time));
    }

    private void dataProcess(List<WebElement> elements, JSONArray output) {
        if(elements.size() == 0) return;

        if(api == TranslatorAPI.GOOGLE) {
            int sentenceCount = 0;

            for (WebElement element : elements) {
                if (element.getText().length() < 7) continue;
                CharSequence cs = OpenKoreanTextProcessorJava.normalize(element.getText());
                List<Sentence> sentences = OpenKoreanTextProcessorJava.splitSentences(cs);
                sentenceCount += sentences.size();
                addOutput(output, sentences);
            }

            System.out.printf(" :: %d개의 번역 문장 발견\n", sentenceCount);
        } else if(api == TranslatorAPI.DEEPL) {
            String data = elements.get(0).getText();
            CharSequence cs = OpenKoreanTextProcessorJava.normalize(data);

            List<Sentence> sentences = OpenKoreanTextProcessorJava.splitSentences(cs);
            System.out.printf(" :: %d개의 번역 문장 발견\n", sentences.size());
            addOutput(output, sentences);
        }
    }

    private void addOutput(JSONArray output, List<Sentence> sentences) {
        for(Sentence s : sentences) {
            output.add(UniqueDict.getInstance().replace(s.text().replace("\n", "")));
        }
    }

    private void save(JSONArray json){
        try {
            BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(output)));
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            JsonElement ge = JsonParser.parseString(json.toJSONString());
            writer.write(gson.toJson(ge));
            writer.flush();
            writer.close();
        } catch(IOException ex) {
            System.out.print("Translator의 저장작업 중 오류가 발생하였습니다.\n");
        }
    }


}
