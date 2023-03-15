package org.example.crawler;

import org.example.crawler.exception.NotFoundContainerException;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.openqa.selenium.WebElement;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;

public class DocumentCrawler extends Crawler {
    private final String[] BLACKLIST_TITLE = {
            "References", "Media", "See also", "Recipe", "Change log", "Categories", "Languages", "Read More"
    };

    HashMap<String, List<String>> contextMap;

    @Override

        contextMap = new HashMap<>();

        String[] contexts = getContextContainer(body).getAttribute("innerHTML").split("(?=<h2>)");
        contextMap.put("Header", parseContext(contexts[0]));
        for(int idx = 1 ; idx < contexts.length ; idx++) {

            String[] split = contexts[idx].split("</h2>", 2);
            String title = getTitle(split[0]);
            if(isBlacklist(title)) continue;

            contextMap.put(title, parseContext(split[1]));
        }

        DocumentList.getInstance().addDocument(docName, contextMap);
    }

    private List<String> parseContext(String context) {
        Elements contexts = getContexts(context);
        List<String> list = new ArrayList<>();
        for(Element e : contexts) {
            if(e.text().trim().equals("")) continue;
            list.add(e.text());
        }
        return list;
    }

    private Elements getContexts(String context) {
        // p : 일반적인 텍스트
        // li : 리스트화 되어 있는 텍스트 (ui, li)
        // i : 인용문?
        return Jsoup.parse(context).select("p, li, i");
    }

    private String getTitle(String context) {
        return Jsoup.parse(context).text();
    }

    private boolean isBlacklist(String title) {
        for(String blacklist : BLACKLIST_TITLE)
            if(blacklist.equalsIgnoreCase(title)) return true;
        return false;
    }
}
