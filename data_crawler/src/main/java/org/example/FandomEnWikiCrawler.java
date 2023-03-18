package org.example;

import org.example.crawler.exception.NotFoundContainerException;
import org.example.crawler.fandomen.*;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

import java.io.File;
import java.io.IOException;
import java.time.Duration;

public class FandomEnWikiCrawler {

    private FandomEnCrawlingQueue queue;

    private final WebDriver driver;
    private final long TIMEOUT = 10L;
    private final long REST_TIME = 60L;

    public static void main(String[] args) {
        new FandomEnWikiCrawler().start();
    }

    private FandomEnWikiCrawler() {
        String DRIVER = "./module/chromedriver_win32/chromedriver.exe";
        System.setProperty("webdriver.chrome.driver", new File(DRIVER).getAbsolutePath());

        ChromeOptions options = new ChromeOptions();
        options.addArguments("headless");
        options.addArguments("--disable-popup-blocking");
        options.addArguments("--remote-allow-origins=*");
        options.addArguments("--disable-gpu");
        driver = new ChromeDriver(options);
    }

    public void start() {
        try {
            queue = new FandomEnCrawlingQueue();
            FandomEnCrawlingQueue cache = queue.loadCategoryCache();
            if(cache == null) {
                String URL_ROOT = "https://leagueoflegends.fandom.com/wiki/Category:Lore";
                queue.add(URL_ROOT);
            } else {
                System.out.printf("저장된 캐시를 불러옵니다. [Categories : %d, Documents : %d]\n", cache.size()[0], cache.size()[1]);
                queue = cache;
            }
        } catch (IOException | ClassNotFoundException e) {
            throw new RuntimeException(e);
        }
        crawl();
    }

    /*
     * [ 위키 크롤링 규칙 ]
     * 1. 위키의 제목 및 컨텍스트는 <main class="page__main" lang="en"> 밑에 위치한다.
     *  1-1) 문서의 카테고리는 <div class="page-header__categories"> 에서 확인할 수 있다. (접혀있는 것이 있을 수 있으니, a href로 체크한다.)
     *  1-2) 문서의 제목은 <h1 class="page-header__title">에서 확인할 수 있다.
     *  1-3) 문서의 내용은 <div class="mw-parser-output">에서 확인할 수 있다.
     *.
     * 2. 문서는 Category:Lore의 하위 문서만 탐색한다.
     *  2-1) 문서 내 버튼에는 접근하지 않는다. ( Lore의 하위문서라면 결과적으로 모두 탐색하게 된다. )
     *  2-2) 카테고리의 mw-parser-output에 <a class="image link-internal">이 있다면 Deque의 앞에 추가한다.
     *  2-3) <div class="category-page__members">에 <a class="category-page__member-link">이 있다면 text의 prefix를 확인한다.
     *    2-3-1) prefix가 Category: 라면 Deque의 뒤에 추가한다.
     *    2-3-2) prefix가 File: 라면 무시한다.
     *  2-4) 들어간 문서의 카테고리에 Alternate Universe [Music Video, Video, Audio]가 있다면 스킵한다.
     *  2-5) 문서는 <h2>를 기준으로 분할한다.
     *   2-5-1) 해당 블럭의 <h2> 내부 텍스트가 [References, Change log]라면 무시한다.
     *   2-5-2) Lore 내부에 여러 페이지가 있는 경우가 있지만, 모두 html에 들어있으므로, 버튼을 누를 필요는 없다.
     *.
     * 3. 위키 사이트에 과한 트래픽 부하를 주지 않기 위해 40개의 문서를 탐색할 때 마다 1분씩 휴식한다.
     * .
     * 4. 위키의 정보들은 CC-BY-SA 규약에 따른다. [ 저작자 표시, 동일 조건 변경 허락 ]
     */
    private void crawl() {
        int documents = 0;
        while(!queue.isEmpty()) {
            String nowURL = queue.poll();
            System.out.printf("[Attempt %d] remain :: (categories : %d, documents : %d)] %s\n", ++documents, queue.size()[0], queue.size()[1], nowURL);

            FandomEnDocumentType docType = FandomEnDocumentType.getType(nowURL);
            if(docType != FandomEnDocumentType.Category && docType != FandomEnDocumentType.Document) {
                System.out.printf("URL [%s]는 분류되지 않은 카테고리입니다.\n", nowURL);
                continue;
            }

            try {
                driver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(TIMEOUT));
                driver.get(nowURL);
            } catch (Exception timeout) {
                System.out.printf("[Document %s] 시간초과되어 다음 문서로 스킵됩니다. (%s)\n", nowURL, timeout.getMessage());
                continue;
            }

            WebElement bodyText = driver.findElement(By.tagName("body"));

            try {
                if (docType == FandomEnDocumentType.Category) {
                    new FandomEnCategoryCrawler().call(queue, bodyText, nowURL);
                } else {
                    new FandomEnDocumentCrawler().call(queue, bodyText, nowURL);
                }
            } catch(NotFoundContainerException ex) {
                System.out.printf("SKIPPED %s\n", nowURL);
            }
        }

        try {
            FandomEnDocumentList.getInstance().save();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        driver.close();
    }

}
