package org.example.crawler;

import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import java.util.Arrays;
import java.util.Deque;
import java.util.List;

public class CategoryCrawler extends Crawler {
// 2. 문서는 Category:Lore의 하위 문서만 탐색한다.
// *  2-2) 카테고리의 mw-parser-output에 <a class="image link-internal">이 있다면 Deque의 앞에 추가한다.
// *  2-3) <div class="category-page__members">에 <a class="category-page__member-link">이 있다면 text의 prefix를 확인한다.
// * *  2-3-1) prefix가 Category: 라면 Deque의 뒤에 추가한다.
// * *  2-3-2) prefix가 File: 라면 무시한다.
    @Override
    protected void execute(CrawlingQueue queue, WebElement body) {

        System.out.println(Arrays.toString(getCategory(body)));

        WebElement top_container = getContextContainer(body);
        List<WebElement> top_btns = top_container.findElements(By.cssSelector("a.image.link-internal"));
        for(WebElement we : top_btns){
            String new_link = we.getAttribute("href");
            System.out.printf("NEW CATEGORY : %s\n", new_link);
            if(new_link != null && new_link.startsWith(WIKI_PREFIX))
                queue.add(new_link);
        }

        WebElement childs = getChildCategories(body);
        List<WebElement> child_categories = childs.findElements(By.className("category-page__member-link"));
        for(WebElement we : child_categories) {
            String new_link = we.getAttribute("href");
            if(new_link != null && new_link.startsWith(WIKI_PREFIX))
                queue.add(new_link);
        }


    }
}
