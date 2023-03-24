package org.example.crawler.fandom;

import org.example.crawler.CrawlingQueue;
import org.example.crawler.CrawlingSearcher;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class FandomSearcher extends CrawlingSearcher {
    class WikiParser {
        String title, path;
        HashMap<String, JSONArray> maps;

        WikiParser(String title) {
            this.title = title;
            path = String.format("/%s/", title);
            maps = new HashMap<>();
        }

        void push(WebElement element) {
            if(!maps.containsKey(path))
                maps.put(path, new JSONArray());

            if(element.getTagName().equals("li") && element.findElements(By.cssSelector(":scope > img")).size() > 0) return;

            String text = element.getText();
            if(text.equals("") || !element.isDisplayed()) {
                text = Jsoup.parse(element.getAttribute("innerHTML")).text();
            }
            text = text
//                    .replaceAll("((?=<).*?(?<=>))+", "")
                    .replaceAll(" {2,}", " ")
                    .trim();
//            System.out.println(text);
            if(text.equals("")) return;
            maps.get(path).add(text);
        }

        void setPath(String tag, String title) {
            // h2면 /root/, h3이면 /root/sub/, h4면 /root/sub/title/
            int count = tag.charAt(1)-'0', index = 0, i = 0, offset;
            if(path.split("/").length == 3) {
                index = path.length();
            } else {
                while (++i < count && (offset = path.substring(index).indexOf('/')) >= 0)
                    index = index + offset + 1;
            }
            String parent = path.substring(0, Math.min(index, path.length()));
            path = String.format("%s%s/", parent, title);
//            System.out.printf("===> Inner New Path : %s\n", path);
        }

        int getDepth() {
            return path.split("/").length;
        }

        JSONObject make() {
            JSONObject object = new JSONObject();
            for(String key : maps.keySet()) {
                if(maps.get(key).size() == 0) continue;
                object.put(key, maps.get(key));
            }
            return object;
        }

    }

    private final By TITLE_SELECTOR = By.cssSelector("#firstHeading");
    private final By CONTENT_SELECTOR = By.cssSelector("#mw-content-text > div.mw-parser-output");
    private final By TABLE_SELECTOR = By.cssSelector("#mw-content-text > div.mw-parser-output > table");

    @Override
    public void search(String docName, CrawlingQueue queue, WebElement element) {
        if(docName.toLowerCase().contains("category"))
            searchCategory(docName, queue, element);
        else
            searchDocument(docName, queue, element);
    }

    private void searchCategory(String docName, CrawlingQueue queue, WebElement element) {
        WebElement docList = element.findElement(By.cssSelector("#mw-content-text > div.category-page__members"));
        List<WebElement> buttons = docList.findElements(By.tagName("a"));
        for(WebElement btn : buttons) {
            String btnTag = btn.getAttribute("title");
            if(passCategory(btnTag))
                continue;
            queue.addQueue(body.URL_PREFIX, btn.getAttribute("href"));
        }
    }

    private void searchDocument(String docName, CrawlingQueue queue, WebElement element) {
        WebElement category = element.findElement(By.cssSelector("body > div.main-container > div.resizable-container > div.page.has-right-rail > main > div.page-header > div.page-header__top > div.page-header__meta"));
        if(!passCategory(category)) return;

        // 존재하지 않는 문서를 걸러냄
        List<WebElement> titles = element.findElements(TITLE_SELECTOR);
        if(titles.size() == 0) {
            System.out.printf("[Document %s] Title을 발견하지 못해 스킵되었습니다.\n", docName);
            return;
        }

        List<WebElement> contents = element.findElements(CONTENT_SELECTOR);
        if(contents.size() == 0) {
            System.out.printf("[Document %s] Content를 발견하지 못해 스킵되었습니다.\n", docName);
            return;
        }

        JSONObject context = new JSONObject();

        // 테이블 파싱
        List<WebElement> tables = element.findElements(TABLE_SELECTOR);
        if(tables.size() > 0) parseTable(context, tables);


        // 문서 카테고리 형식을 유지하며 저장
        List<WebElement> childs = contents.get(0).findElements(By.cssSelector(":scope > *"));
        parseDetails(context, new JSONArray(), new JSONObject(), childs, null, 0);

        body.addCrawlingData(docName, context);
    }

    private void parseTable(JSONObject context, List<WebElement> tables) {

        JSONArray quoteArray = new JSONArray();
        JSONArray tableArray = new JSONArray();
        JSONArray character = new JSONArray();


        for (int n = 0; n < tables.size(); n++) {
            WebElement tableElement = tables.get(n);
            String className = tableElement.getAttribute("class");

            if (className.equals("")) {
                List<WebElement> trs = tableElement.findElements(By.cssSelector("tbody > tr"));
                if (trs.size() == 3) { // Quote
                    JSONObject parse = parseQuote(tableElement);
                    if (parse == null || parse.size() == 0) continue;
                    quoteArray.add(parse);
                } else { // table
                    JSONArray table = new JSONArray();

                    List<String> keys = new ArrayList<>();
                    List<WebElement> ths = trs.get(0).findElements(By.cssSelector("th"));
                    for (WebElement td : ths) keys.add(td.getText());
                    String[] keysArray = keys.toArray(new String[0]);

                    for (int idx = 1; idx < trs.size(); idx++) {
                        JSONObject elm = new JSONObject();
                        List<WebElement> tds = trs.get(idx).findElements(By.cssSelector("td"));

                        for (int key = 0; key < tds.size(); key++) {
                            String keyIndex = keysArray.length > key ? keysArray[key] : String.format("index %d", key);
                            elm.put(keyIndex, tds.get(key).getText());
                        }
                        table.add(elm);
                    }
                    tableArray.add(table);
                }
            } else if (className.equals("character-table")) {
                JSONObject cinfo = parseCharacterTable(tableElement);
                if (cinfo == null || cinfo.size() == 0) continue;
                character.add(cinfo);
            }
        }

        if (quoteArray.size() > 0)
            context.put("quotes", quoteArray);

        if (tableArray.size() > 0)
            context.put("tables", tableArray);

        if (character.size() > 0)
            context.put("characters", character);
    }

    private void parseDetails(JSONObject context, JSONArray innerContext, JSONObject special, List<WebElement> elements, WikiParser wp, int offset) {
//        if(wp!=null) System.out.printf("[OFF : %d] Title : %s\n", offset, wp.title);

        for(WebElement child : elements) {
            String tagName = child.getTagName();
            // table은 전처리했으니 추가 처리하지 않음
            if(tagName.equals("table")) continue;

            // h2를 만나면 새로운 Tree를 구성
            if (tagName.equals("h2")) {
                if (wp != null) {
                    JSONObject wpObject = wp.make();
                    if(wpObject.size() > 0)
                        innerContext.add(wpObject);
                }

                wp = exceptTitle(child.getText()) ? null : new WikiParser(child.getText());
                continue;
            }

            // 만약 트리가 구성되어있지 않다면 그 값은 무의미하게 처리됨.
            if (wp == null) continue;


            if(tagName.equals("div") && child.getAttribute("class").equals("tabber wds-tabber")) { // 여러 페이지 있는 항목 탐색

                List<WebElement> categoryList = child.findElements(By.cssSelector(":scope > div.wds-tabs__wrapper.with-bottom-border > ul > li"));
                String[] indexes = new String[categoryList.size()];
                for(int i = 0 ; i < indexes.length ; i++) indexes[i] = categoryList.get(i).getText();

                List<WebElement> divContent = child.findElements(By.cssSelector(":scope > div.wds-tab__content"));
                int depth = wp.getDepth();
                for(int idx = 0 ; idx < categoryList.size() ; idx++) {
                    wp.setPath(String.format("h%d", depth+1), indexes[idx]);

                    List<WebElement> ps = divContent.get(idx).findElements(By.xpath("./*"));
                    parseDetails(context, innerContext, special, ps, wp, 1);
                }

            } else if (tagName.startsWith("h")) { // h Tag는 자식트리
                if(offset > 0) {
                    tagName = "h" + (char)(tagName.charAt(1)+offset);
                }
                String title = child.isDisplayed() ? child.getText() : Jsoup.parse(child.getAttribute("innerHTML")).text();
                wp.setPath(tagName, title.trim());
            } else if (!tagName.startsWith("d") && !tagName.startsWith("figure")) { // d Tag는 다른 문서의 안내 등의 텍스트 포함
                wp.push(child);
            }
        }

        if(wp != null) {
            JSONObject wpObject = wp.make();
            if(wpObject.size() > 0)
                innerContext.add(wpObject);
        }

        if(special.size() > 0)
            context.put("special", special);
        context.put("inner", innerContext);
    }



    private JSONObject parseQuote(WebElement quote) {
        JSONObject map = new JSONObject();
        List<WebElement> is =quote.findElements(By.tagName("i"));
        if(is.size() == 0) return null;
        String context = is.get(0).getText();
        List<WebElement> trs = quote.findElements(By.cssSelector("tbody > tr"));
        String writer = trs.get(1).getText();
        if(writer.length() > 2) {
            writer = writer
                    .substring(1)
                    .replace(" ", "_")
                    .replaceAll("_{2,}", " ")
                    .replaceAll("^[0-9]+\\n_", "")
                    .trim();
        } else {
            writer = "Unknown";
        }

        map.put("writer", writer);
        map.put("context", context);
        return map;
    }

    private JSONObject parseCharacterTable(WebElement table) {
        JSONObject map = new JSONObject();
        List<WebElement> tableElements = table.findElements(By.cssSelector("tbody > tr"));
        if(tableElements.size() < 1) return null;
        map.put("name", tableElements.get(0).getText());
        for(int idx = 1 ; idx < tableElements.size() ; idx++) {
            WebElement child = tableElements.get(idx);
            String key = child.findElement(By.cssSelector("th")).getText();
            String val = child.findElement(By.cssSelector("td")).getText();
            if(key.equalsIgnoreCase("referenced")) {
                val = "";
                for (WebElement a : child.findElements(By.cssSelector("td > a"))) {
                    val = val + " " + a.getText();
                }
                if(val.equals("")) val = "None";
            }

            val = val.replaceAll(" {2,}", " ");
            if(val.charAt(0) == ' ') val = val.substring(1);
            map.put(key, val.trim());
        }

        return map;
    }
    
    private boolean passCategory(WebElement category) {
        List<WebElement> categories = category.findElements(By.tagName("a"));
        for(WebElement cat : categories) {
            String text = cat.getAttribute("title");
            if(!text.startsWith("Category")) continue;
            if(passCategory(text))
                return false;
        }

        return true;
    }

    // 카테고리 블랙리스트
    private boolean passCategory(String text) {
        Pattern except = Pattern.compile("(comic|tabletop|audio|video|image|icon|voice|chroma|tile|loading|skin|circle|square|item|abilities|games|" +
                "staff|file|template|user|old|event|cosmetics|soundtrack|content|league of legends" +
                "|legends of runeterra|little|teamfight|patch history|lol history|poc champions|wild rift|development|strategies|champion trivia)");
        return except.matcher(text.toLowerCase()).find();
    }

    // 문서 목차 블랙리스트
    private synchronized boolean exceptTitle(String title) {
        Pattern except = Pattern.compile("(references|trivia|media|see also|recipe|change log|categories|languages|read more|history)");
        return except.matcher(title.toLowerCase()).find();
    }
}
