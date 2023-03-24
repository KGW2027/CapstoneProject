package org.example.crawler.fandom;

import org.example.crawler.CrawlingQueue;
import org.example.crawler.CrawlingSearcher;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import java.util.HashMap;
import java.util.List;
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
            String text = element.getText().replaceAll(" {2,}", " ").trim();
            if(text.equals("")) return;
            maps.get(path).add(text);
        }

        void setPath(String tag, String title) {
            // h2면 /, h3이면 /~/, h4면 /~/~/
            int count = Integer.parseInt(tag.replace("h", "")), index = 0, i = 0;
            while(i++ < count) index = index + path.substring(index).indexOf('/');
            String parent = path.substring(0, index+1);
            path = parent + title;
        }

        JSONObject make() {
            JSONObject object = new JSONObject();
            for(String key : maps.keySet())
                object.put(key, maps.get(key));
            return object;
        }
    }

    private final By TITLE_SELECTOR = By.cssSelector("#firstHeading");
    private final By CONTENT_SELECTOR = By.cssSelector("#mw-content-text > div.mw-parser-output");
    private final By QUOTE_SELECTOR = By.cssSelector("#mw-content-text > div.mw-parser-output > table");

    @Override
    public void search(String docName, CrawlingQueue queue, WebElement element) {
        if(docName.contains("category"))
            searchCategory(docName, queue, element);
        else
            searchDocument(docName, queue, element);
    }

    private void searchCategory(String docName, CrawlingQueue queue, WebElement element) {
        WebElement docList = element.findElement(By.cssSelector("#mw-content-text > div.category-page__members"));
        List<WebElement> buttons = docList.findElements(By.tagName("a"));
        for(WebElement btn : buttons) {
            String btnTag = btn.getAttribute("title");
            if(btnTag.indexOf(':') > 0 && exceptTitle(btnTag.split(":")[0])) continue;
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

        // 인용구가 있을 시 따로 분리
        List<WebElement> quotes = element.findElements(QUOTE_SELECTOR);
        if(quotes.size() > 0) {
            JSONArray quoteArray = new JSONArray();
            for(int n = 0 ; n < quotes.size() ; n++) {
                WebElement quote = quotes.get(n);
                JSONObject parse = parseQuote(quote);
                if(parse == null) continue;
                quoteArray.add(parseQuote(quote));
            }
            context.put("quotes", quoteArray);
        }

        // 문서 카테고리 형식을 유지하며 저장
        List<WebElement> childs = contents.get(0).findElements(By.cssSelector(":scope > *"));
        WikiParser wp = null;
        JSONArray innerContexts = new JSONArray();
        for(WebElement child : childs) {
            String tagName = child.getTagName();
            if (tagName.equalsIgnoreCase("table")) continue;

            if (tagName.equals("h2")) {
                if (wp != null)
                    innerContexts.add(wp.make());

                wp = exceptTitle(child.getText()) ? null : new WikiParser(child.getText());
                continue;
            }

            if (wp == null) continue;

            if (tagName.startsWith("h")) {
                wp.setPath(tagName, child.getText().trim());
            } else if (!tagName.startsWith("d")) { // d Tag는 다른 문서의 안내 등의 텍스트 포함
                wp.push(child);
            }
        }
        context.put("inner", innerContexts);

        body.addCrawlingData(docName, context);
    }

    private JSONObject parseQuote(WebElement quote) {
        JSONObject map = new JSONObject();
        List<WebElement> is =quote.findElements(By.tagName("i"));
        if(is.size() == 0) return null;
        String context = is.get(0).getText();
        String writer = quote.findElement(By.cssSelector("tbody > tr:nth-child(2) > td > span > span:nth-child(2) > a")).getText();

        writer = writer.replace(" ", "_").toLowerCase();
        map.put("writer", writer);
        map.put("context", context);
        return map;
    }
    
    private boolean passCategory(WebElement category) {
        List<WebElement> categories = category.findElements(By.tagName("a"));
        Pattern except = Pattern.compile("(comic|tabletop|audio|video|image|icon|voice|chroma|tile|loading|skin|circle|square|item|abilities|games|staff|file)");
        for(WebElement cat : categories) {
            String text = cat.getAttribute("title");
            if(!text.startsWith("Category")) continue;
            if(except.matcher(text).find())
                return false;
        }

        return true;
    }

    private boolean exceptTitle(String title) {
        Pattern except = Pattern.compile("(references|trivia|media|see also|recipe|change log|categories|languages|read more)");
        return except.matcher(title.toLowerCase()).find();
    }
}
