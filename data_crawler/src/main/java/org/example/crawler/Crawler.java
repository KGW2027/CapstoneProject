package org.example.crawler;

import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import java.util.List;

public abstract class Crawler {
    protected abstract void execute(CrawlingQueue queue, WebElement body);
    public void call(CrawlingQueue queue, WebElement body, String url) {
        docName = url;
        execute(queue, body);
    }

    private final String CONTAINER_CLASS = "mw-parser-output";
    private final String CATEGORIES_CLASS = "category-page__members";

    protected final String WIKI_PREFIX = "https://leagueoflegends.fandom.com/wiki/";

    protected String docName;

    protected WebElement getContextContainer(WebElement body) {
        List<WebElement> div = body.findElements(By.className(CONTAINER_CLASS));
        if(div.size() > 1) {
            System.out.println("mw-parser-output이 " + div.size() + "개 인 문서가 존재함.");
        }
        return div.get(0);
    }

    protected WebElement getChildCategories(WebElement body) {
        List<WebElement> div = body.findElements(By.className(CATEGORIES_CLASS));
        if(div.size() > 1) {
            System.out.println("category-page__members이 " + div.size() + "개 인 문서가 존재함.");
        }
        return div.get(0);
    }

    protected String[] getCategory(WebElement body) {
        WebElement container = body.findElement(By.className("page-header__categories"));
        String context = container.getText().replace("in:", "");
        return context.split(", ");
    }
}
