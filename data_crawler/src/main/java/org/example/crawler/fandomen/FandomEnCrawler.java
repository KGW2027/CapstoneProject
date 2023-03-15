package org.example.crawler.fandomen;

import org.example.crawler.exception.NotFoundContainerException;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import java.util.List;

public abstract class FandomEnCrawler {
    protected abstract void execute(FandomEnCrawlingQueue queue, WebElement body) throws NotFoundContainerException;
    public void call(FandomEnCrawlingQueue queue, WebElement body, String url) throws NotFoundContainerException {
        int lastSep = url.lastIndexOf('/');
        docName = url.substring(lastSep+1);
        execute(queue, body);
    }

    private final String CONTAINER_CLASS = "mw-parser-output";
    private final String CATEGORIES_CLASS = "category-page__members";
    protected final String[] CATEGORY_BLACK_LIST = {
            "comics", "tabletop", "audio", "videos", "images", "icon", "voice-over", "chroma", "tile",
            "loading", "skin", "circle", "square", "items"
    };

    protected final String WIKI_PREFIX = "https://leagueoflegends.fandom.com/wiki/";

    protected String docName;

    protected WebElement getContextContainer(WebElement body) throws NotFoundContainerException {
        List<WebElement> div = body.findElements(By.className(CONTAINER_CLASS));
        if(div.size() > 1) {
            System.out.println("mw-parser-output이 " + div.size() + "개 인 문서가 존재함.");
        }
        if(div.size() == 0) throw new NotFoundContainerException(docName);
        return div.get(0);
    }

    protected WebElement getChildCategories(WebElement body) throws NotFoundContainerException {
        List<WebElement> div = body.findElements(By.className(CATEGORIES_CLASS));
        if(div.size() > 1) {
            System.out.println("category-page__members이 " + div.size() + "개 인 문서가 존재함.");
        }
        if(div.size() == 0) throw new NotFoundContainerException(docName);
        return div.get(0);
    }

    protected String[] getCategory(WebElement body) {
        // <div class="page-header__categories">
        WebElement container = body.findElement(By.className("page-header__categories"));
        String context = container.getText().replace("in:", "").toLowerCase();
        String[] split = context.split(", ");
        for(String blacklist : CATEGORY_BLACK_LIST) {
            if (context.contains(blacklist.toLowerCase())){
                System.out.print("블랙리스트에 포함된 카테고리가 발견되어 탐색이 스킵됩니다.\n");
                return new String[0];
            }
        }
        return split;
    }

    protected boolean isLoreCategory(WebElement body) {
        String[] categories = getCategory(body);
        if(docName.startsWith("Category")) {
            String thisCategory = docName.split(":")[1];
            return FandomEnCategories.getInstance().addCategory(thisCategory, categories);
        }

        return FandomEnCategories.getInstance().validLore(categories);
    }

    protected boolean isBlacklistTitle(String url) {
        for(String blacklist : CATEGORY_BLACK_LIST)
            if(url.contains(blacklist)) return true;
        return false;
    }
}
