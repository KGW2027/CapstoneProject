package org.example.crawler.kouniverse;

import org.example.crawler.CrawlingQueue;
import org.example.crawler.CrawlingSearcher;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.util.Arrays;
import java.util.List;

public class UniverseKoSearcher extends CrawlingSearcher {

    @Override
    public void search(String docName, CrawlingQueue queue, WebElement element) {

        initialWait(docName);
        addButtons(queue, element);

        // 문서 정보 획득
//        String[] descs = inner.split("(?=<h[1-2]>)");
//        body.addCrawlingData(docName, parseTexts());
        parse(docName, element);
    }

    private synchronized void addButtons(CrawlingQueue queue, WebElement element) {
        int added = 0;
        for(WebElement button : element.findElements(By.tagName("a"))) {
            try {
                String href = button.getAttribute("href").toLowerCase();
                if (!href.startsWith(body.URL_PREFIX) || href.contains("#")) continue;
                queue.addQueue(body.URL_PREFIX, href);
                ++added;
            } catch(Exception ignored) { /* 접근 불가능한 Element에 접근한 경우 */ }
        }
    }

    private void waitLoad(ExpectedCondition condition) {
        try {
            body.getDriver().waitLoad(condition, 10L);
        } catch (Exception e) {
        }
    }

    private void initialWait(String docName) {
        if (docName.startsWith("/champion/")) {
            waitLoad(ExpectedConditions.presenceOfElementLocated(By.className("quote_2507")));
        } else if(docName.equals("/champions/")) {
            waitLoad(ExpectedConditions.presenceOfElementLocated(By.cssSelector("div > article > div:nth-child(2) > ul")));
        } else if (docName.startsWith("/region/")) {
            waitLoad(ExpectedConditions.presenceOfElementLocated(By.className("introDescription_hkI3")));
        } else if (docName.startsWith("/story/")) {
            waitLoad(ExpectedConditions.presenceOfElementLocated(By.className("content_2ybc")));
        } else if (docName.startsWith("/race/")) {
            String format = String.format("#%s", docName.replace("/race/", "").replace("/", ""));
            waitLoad(ExpectedConditions.presenceOfElementLocated(By.cssSelector(format)));
        } else {
            System.out.printf("EXPECTED : %s\n", docName);
        }

    }

    private void parse(String docName, WebElement element) {
        try {
            if (docName.startsWith("/champion/")) {
                body.addCrawlingData(docName, parseChampion(element));
            } else if (docName.startsWith("/region/")) {
                body.addCrawlingData(docName, parseRegion(element));
            } else if (docName.startsWith("/story/")) {
                body.addCrawlingData(docName, parseStory(element));
            } else if (docName.startsWith("/race/")) {
                String format = String.format("#%s", docName.replace("/race/", "").replace("/", ""));
                body.addCrawlingData(docName, parseRace(format, element));
            } else {
                System.out.printf("EXPECTED : %s\n", docName);
            }
        } catch (Exception ex) {
            System.out.printf("문서 %s에서 오류 발생 :: %s\n", docName, ex.getClass().toString());
        }
    }

    private JSONObject parseRace(String format, WebElement element) {
        JSONObject jo = new JSONObject();

        WebElement story = element.findElement(By.cssSelector(format));
        String context = cleanHtml(story.getAttribute("innerHTML"));
        JSONArray array = new JSONArray();

        for(String line : context.split("\n")) {
            if (line.trim().equals("")) continue;
            array.add(line);
        }
        jo.put("context", array);

        return jo;
    }

    private JSONObject parseChampion(WebElement element) {
        JSONObject jo = new JSONObject();

        String[] cq = new String[0];
        do {
            if(cq.length > 0) {
                try {
                    Thread.sleep(5 * 1000);
                } catch (InterruptedException e) {
                    throw new RuntimeException(e);
                }
            }
            waitLoad(ExpectedConditions.presenceOfElementLocated(By.className("quote_2507")));

            WebElement championQuoteElement = element.findElement(By.className("quote_2507"));
            cq = cleanHtml(championQuoteElement.getAttribute("innerHTML")).split("~ ");
        } while(cq[0].replace("\n", "").trim().equals(""));
        JSONObject championQuote = new JSONObject();
        championQuote.put("quote", cq[0].replace("\n", ""));
        championQuote.put("by", cq[1].replace("\n", ""));
        jo.put("quotes", championQuote);

        WebElement championDescription = element.findElement(By.className("biographyText_3-to"));
        WebElement championRegion = element.findElement(By.className("factionText_EnRL"));
        jo.put("description", championDescription.getText());
        jo.put("region", championRegion.getText().replace("지역", ""));

        return jo;
    }

    private JSONObject parseRegion(WebElement element) {
        JSONObject jo = new JSONObject();

        waitLoad(ExpectedConditions.presenceOfElementLocated(By.className("introDescription_hkI3")));

        WebElement regionDescription = element.findElement(By.className("introDescription_hkI3"));
        String description = regionDescription.getText();
        jo.put("description", description.split("\n"));

        return jo;
    }

    private JSONObject parseStory(WebElement element) {
        JSONObject jo = new JSONObject();

        waitLoad(ExpectedConditions.presenceOfElementLocated(By.className("inner_fkqi")));

        String titles = cleanHtml(element.findElement(By.className("inner_fkqi")).getAttribute("innerHTML"));
        List<String> titleList = Arrays.stream(titles.split("\n")).filter(t -> !t.equals("")).toList();
        jo.put("titles", titleList);

        WebElement contents = element.findElement(By.className("content_2ybc"));
        JSONArray document = new JSONArray();
        for(WebElement content : contents.findElements(By.className("root_3Kft"))) {
            for(String line : cleanHtml(content.getAttribute("innerHTML")).split("\n")) {
                if(line.trim().equals("") || titleList.contains(line)) continue;
                document.add(line);
            }
        }
        jo.put("document", document);

        return jo;
    }

    private String cleanHtml(String text) {
        return text.replaceAll("<.*?>", "\n").replaceAll("\n+", "\n");
    }

}
