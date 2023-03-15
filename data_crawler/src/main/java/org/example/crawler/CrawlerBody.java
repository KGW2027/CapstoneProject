package org.example.crawler;

import org.openqa.selenium.By;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.io.File;
import java.io.IOException;
import java.time.Duration;

public class CrawlerBody {

    private final String URL_PREFIX;
    private WebDriver driver;
    private CrawlingDatas cDatas;
    private CrawlingQueue queue;
    private CrawlingSearcher searcher;
    private String waitCss, name;

    public CrawlerBody(String name, String urlPrefix, CrawlingQueue queue, CrawlingSearcher searcher) {
        this.cDatas = new CrawlingDatas(name);
        this.name = name;
        this.URL_PREFIX = urlPrefix.toLowerCase();
        this.queue = queue;
        this.searcher = searcher.setBody(this);
        this.waitCss = "";

        this.queue.addQueue(URL_PREFIX);
        this.searcher.addExpectPrefix(URL_PREFIX);

        String DRIVER = "./module/chromedriver_win32/chromedriver.exe";
        System.setProperty("webdriver.chrome.driver", new File(DRIVER).getAbsolutePath());

        ChromeOptions options = new ChromeOptions();
        options.addArguments("headless");
        options.addArguments("--disable-popup-blocking");
        options.addArguments("--remote-allow-origins=*");
        options.addArguments("--disable-gpu");
        driver = new ChromeDriver(options);
    }

    public CrawlerBody setWaitCss(String waitCss) {
        this.waitCss = waitCss;
        return this;
    }

    public void addCrawlingData(String docName, CrawlingData data) {
        cDatas.put(docName, data);
    }

    public void start() {
        int attempt = 0;
        while(!queue.isEmpty()) {
            if(attempt % 100 == 0) {
                try {
                    cDatas.save(name);
                } catch (IOException e) {
                    System.out.printf("[저장 중 에러가 발생했습니다. :: %s]", e.getMessage());
                }
            }

            String url = queue.poll();
            if(!isTargetDocs(url)) continue;

            System.out.printf("[Attempt %04d] %s\n", ++attempt, url);

            try {
                driver.get(url);
                if(!waitCss.equals("")) {
                    new WebDriverWait(driver, Duration.ofSeconds(10L)).until(ExpectedConditions.presenceOfElementLocated(By.cssSelector(waitCss)));
                }
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

        driver.close();
    }

    private boolean isTargetDocs(String url) {
        return url.toLowerCase().startsWith(URL_PREFIX);
    }
}
