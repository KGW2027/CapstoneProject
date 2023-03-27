package org.example.crawler;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.openqa.selenium.WebElement;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public abstract class CrawlingSearcher {

    private List<String> prefixes;
    protected CrawlerBody body;

    public CrawlingSearcher setBody(CrawlerBody body) {
        this.body = body;
        return this;
    }

    public abstract void search(String docName, CrawlingQueue queue, WebElement element);

    public void addExpectPrefix(String url) {
        if(prefixes == null) prefixes = new ArrayList<>();
        prefixes.add(url.toLowerCase());
    }

    protected boolean isExpect(String url) {
        url = url.toLowerCase();
        for(String prefix : prefixes)
            if(prefix.startsWith(url)) return true;
        return false;
    }

    protected boolean isExternalUrl(String url) {
        if(url.startsWith("http")) return !isExpect(url);
        return url.equals("") || url.startsWith("javascript") || url.startsWith("#");
    }

    protected CrawlingData parseTexts(String[] split) {
        CrawlingData map = new CrawlingData();
        map.add("Header", parseContext(split[0]));
        for(int idx = 1 ; idx < split.length ; idx++) {
            String[] context = split[idx].split("</h[1-2]>", 2);
            String title = getTitle(split[0]);
            map.add(title, parseContext(context[1]));
        }
        return map;
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
        return Jsoup.parse(context).select("p, li, i");
    }

    private String getTitle(String context) {
        return Jsoup.parse(context).text();
    }
}
