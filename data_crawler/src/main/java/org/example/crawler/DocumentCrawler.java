package org.example.crawler;

import org.openqa.selenium.WebElement;

import java.util.Arrays;
import java.util.Deque;

public class DocumentCrawler extends Crawler {
    @Override
    protected void execute(CrawlingQueue queue, WebElement body) {
        System.out.println(Arrays.toString(getCategory(body)));
    }
}
