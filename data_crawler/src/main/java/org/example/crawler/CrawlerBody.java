package org.example.crawler;

import org.json.simple.JSONObject;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.io.File;
import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/*
 * CrawlerBody is Controller of crawler.
 * 1. Main method creates CrawlerBody (with CrawlingQueue & Searcher, post urls )
 * 2. CrawlerBody.start() -> check Queue, turn on browser, send data to Searcher
 * 3. Searcher Checks context, and data processing result send to 'body.cDatas', and add queue
 * 4. loop
 * 5. if end to search, save file
 */

public class CrawlerBody {

    public final String URL_PREFIX;
    private WebDriver driver;
    private CrawlingDatas cDatas;
    private CrawlingQueue queue;
    private CrawlingSearcher searcher;
    private ChromeOptions options;
    private List<String> blacklists;
    private String waitCss, name;

    public CrawlerBody(String name, String urlPrefix, CrawlingQueue queue, CrawlingSearcher searcher) {
        this.cDatas = new CrawlingDatas(name);
        this.name = name;
        this.URL_PREFIX = urlPrefix.toLowerCase();
        this.queue = queue;
        this.searcher = searcher.setBody(this);
        this.waitCss = "";
        this.blacklists = new ArrayList<>();

//        this.queue.addQueue(URL_PREFIX);
        this.searcher.addExpectPrefix(URL_PREFIX);

        String DRIVER = "./module/chromedriver_win32/chromedriver.exe";
        System.setProperty("webdriver.chrome.driver", new File(DRIVER).getAbsolutePath());

        ChromeOptions options = new ChromeOptions();
//        options.addArguments("headless");
        options.addArguments("--disable-popup-blocking");
        options.addArguments("--remote-allow-origins=*");
        options.addArguments("--disable-gpu");

        this.options = options;
    }

    /**
     * 크롤러가 웹 사이트를 탐색했을 때 기다릴 Element의 CSS 작성 ( By.cssSelector에 사용됨 )
     * @param waitCss 기다릴 Element의 css
     * @return self
     */
    public CrawlerBody setWaitCss(String waitCss) {
        this.waitCss = waitCss;
        return this;
    }

    /**
     * 탐색할 큐의 초기값을 입력. (위키의 최상위 카테고리 등..)
     * @param url url의 prefix부분을 뺴고 그 뒤만 입력
     * @return self
     */
    public CrawlerBody addQueueManually(String url) {
        this.queue.addQueue(URL_PREFIX, url.toLowerCase());
        return this;
    }

    /**
     * URL에 포함될 경우 탐색을 스킵할 블랙리스트 작성
     * @param blacklist contains로 탐색할 텍스트
     * @return self
     */
    public CrawlerBody addBlacklist(String blacklist) {
        this.blacklists.add(blacklist.toLowerCase());
        return this;
    }

    /**
     * 브라우저를 Headless로 실행할지 결정.
     * @return self
     */
    public CrawlerBody setHeadless() {
        options.addArguments("headless");
        return this;
    }

    /**
     * 외부에서 크롤링 데이터를 받기위한 메소드
     * @param docName 문서 제목
     * @param data 문서 데이터
     */
    public void addCrawlingData(String docName, CrawlingData data) {
        cDatas.put(docName, data);
    }

    public void addCrawlingData(String docName, JSONObject data) {
        cDatas.put(docName, data);
    }

    /**
     * URL에 블랙리스트의 단어들이 들어가있는지 확인함.
     * @param url 타겟 URL
     * @return 포함 여부
     */
    private boolean isBlacklist(String url) {
        url = url.toLowerCase().trim();
        for(String blacklist : blacklists)
            if(url.contains(blacklist)) return true;
        return false;
    }

    /**
     * URL이 크롤러의 탐색 대상이 맞는지 확인함.
     * @param url 타겟 URL
     * @return 대상 여부
     */
    private boolean isTargetDocs(String url) {
        return url.toLowerCase().startsWith(URL_PREFIX) && !isBlacklist(url);
    }

    public void start() {
        driver = new ChromeDriver(options);
        if(waitCss.equals("")) waitCss = "body";

        int attempt = 0;
        while(!queue.isEmpty()) {
            if(attempt % 100 == 0) {
                try {
                    cDatas.clearName();
                    cDatas.appendDate();
                    cDatas.appendNum(attempt);
                    cDatas.save();
                } catch (IOException e) {
                    System.out.printf("[저장 중 에러가 발생했습니다. :: %s]\n", e.getMessage());
                }
            }

            String url = queue.poll();
            if(!isTargetDocs(url)) continue;

            System.out.printf("[Attempt %04d] %s\n", ++attempt, url);

            try {
                driver.get(url);
                new WebDriverWait(driver, Duration.ofSeconds(10L)).until(ExpectedConditions.presenceOfElementLocated(By.cssSelector(waitCss)));
            } catch (TimeoutException timeout) {
                System.out.printf("[URL %s]에 대한 탐색 중 시간초과 발생\n", url);
            }

            try {
                searcher.search(url.replace(URL_PREFIX, ""), queue, driver.findElement(By.tagName("body")));
            } catch (Exception ex) {
                System.out.printf("[URL %s]에 대한 탐색 중 오류 발생 :: %s\n", url, ex.getMessage());
            }

            System.out.printf("현재 Queue size => [PRE] %d [POST] %d\n", queue.size()[0], queue.size()[1]);
        }

        cDatas.clearName();
        cDatas.appendDate();
        cDatas.appendNum(attempt);
        try {
            cDatas.save();
        } catch (IOException e) {
            System.out.printf("[최종 저장 중 에러가 발생했습니다.ㅠㅠ :: %s]\n", e.getMessage());
        }

        driver.close();
    }
}
