package org.example.crawler;

import org.openqa.selenium.WebElement;

import java.util.ArrayList;
import java.util.List;

public class CrawlingSearcher {

    private List<String> prefixes;

    public void search(CrawlingQueue queue, WebElement element) {

    }

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
        return url.equals("") || url.startsWith("http") || url.startsWith("javascript") || url.startsWith("#");
    }
}
