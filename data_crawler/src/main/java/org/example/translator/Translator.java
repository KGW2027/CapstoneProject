package org.example.translator;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.example.ChromeDriver;
import org.example.translator.processors.UniverseParser;
import org.json.simple.JSONArray;
import org.json.simple.parser.ParseException;
import org.openqa.selenium.By;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebElement;

import java.io.*;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

public class Translator {

    public static void main(String[] args) {
        new Translator()
                .setStartLanguage(Language.ENGLISH)
                .setEndLanguage(Language.KOREAN)
//                .initTexts(new FandomJSONParser())
                .initTexts(new UniverseParser())
                .setAutosaveTerm(100)
                .translate()
        ;
    }

    private final String Translator_URL = "https://translate.google.co.kr/?sl={START}&tl={END}&text={TEXT}&op=translate";

    private ChromeDriver driver;
    private String targetURL;
    private HashSet<String> texts;
    private File output;
    private int saveTerm;

    private Translator() {
        driver = new ChromeDriver()
                .setTimeout(10L)
                .setWait(By.className("ryNqvb"))
                .enableHeadlessMode()
                .init()
                ;
        targetURL = Translator_URL;
        texts = new HashSet<>();
        saveTerm = -1;
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


    public void translate() {
        if (output == null) {
            throw new NullPointerException("번역 작업을 시작하기 전, initTexts를 먼저 진행해주세요.");
        }

        System.out.printf("%d개 문장을 발견하였습니다. 번역작업을 시작합니다.\n", texts.size());
        StringBuilder translate = new StringBuilder();

        List<String> requests = new ArrayList<>();
        for (String line : texts) {
            if (translate.length() + line.length() > 4500) {
                requests.add(translate.toString());
                translate.setLength(0);
            }
            translate.append(line).append("\n");
        }
        if (translate.length() > 0) requests.add(translate.toString());

        JSONArray outputArray = new JSONArray();

        for (int idx = 0; idx < requests.size(); idx++) {
            String req = requests.get(idx);
            if(req.contains("/") || req.contains("%")) {
                req = URLEncoder.encode(req, StandardCharsets.UTF_8);
            }
            System.out.printf("[%d / %d] %.2f%%  :: Request %d chars", idx + 1, requests.size(), 100f * (idx + 1) / requests.size(), req.length());
            String request = targetURL.replace("{TEXT}", req);
            try {
                driver.connect(request);
            } catch(TimeoutException timeout) {
                System.out.println(" :: TIMEOUT");
                continue;
            }

            List<WebElement> elements = driver.findElements(By.className("ryNqvb"));
            System.out.printf(" :: %d개의 번역 문장 발견\n", elements.size());
            if (elements.size() == 0){
                continue;
            }

            for (WebElement element : elements) {
                if (element.getText().length() < 7) continue;
                String text = element.getText();
                outputArray.add(text);
            }

            if (saveTerm > 0 && (idx > 0 && idx % saveTerm == 0)) {
                save(outputArray);
            }
        }

        save(outputArray);
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
