package org.example.crawler;

import org.example.ChromeDriver;
import org.json.simple.JSONObject;
import org.openqa.selenium.By;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

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
//    private WebDriver driver;
    private CrawlingDatas crawlDatas;
    private CrawlingQueue queue;
    private CrawlingSearcher searcher;
    private List<String> blacklists;
    private String waitCss;
    private int threadCount, attempt;

    private ChromeDriver driver;

    public CrawlerBody(String name, String urlPrefix, CrawlingQueue queue, CrawlingSearcher searcher) {
        this.crawlDatas = new CrawlingDatas(name);
        this.URL_PREFIX = urlPrefix.toLowerCase();
        this.queue = queue;
        this.searcher = searcher.setBody(this);
        this.waitCss = "";
        this.blacklists = new ArrayList<>();
        this.threadCount = 1;
        this.attempt = 0;

        this.searcher.addExpectPrefix(URL_PREFIX);
        driver = new ChromeDriver()
                .setTimeout(10L);
    }

    /**
     * 크롤러가 웹 사이트를 탐색했을 때 기다릴 Element의 CSS 작성 ( By.cssSelector에 사용됨 )
     * @param waitCss 기다릴 Element의 css
     * @return self
     */
    public CrawlerBody setWaitCss(String waitCss) {
        this.driver.setWait(ExpectedConditions.presenceOfElementLocated(By.cssSelector(waitCss)));
        return this;
    }

    /**
     * 탐색할 큐의 초기값을 입력. (위키의 최상위 카테고리 등..)
     * @param url url의 prefix부분을 뺴고 그 뒤만 입력
     * @return self
     */
    public CrawlerBody addQueueManually(String url) {
        this.queue.addQueue(URL_PREFIX, url);
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
        this.driver.enableHeadlessMode();
        return this;
    }

    /**
     * 동시에 몇 개의 브라우저로 크롤링을 진행할 지 정한다.
     * @param count 병렬 작업 개수
     * @return self
     */
    public CrawlerBody setThreadCount(int count) {
        this.threadCount = count;
        return this;
    }

    /**
     * 외부에서 크롤링 데이터를 받기위한 메소드
     * @param docName 문서 제목
     * @param data 문서 데이터
     */
    public synchronized void addCrawlingData(String docName, CrawlingData data) {
        crawlDatas.put(docName, data);
    }

    public synchronized void addCrawlingData(String docName, JSONObject data) {
        crawlDatas.put(docName, data);
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

    /**
     * 저장
     * @param attempt 탐색한 문서 수
     */
    private synchronized void save(int attempt) {
        try {
            crawlDatas.clearName();
            crawlDatas.appendDate();
            crawlDatas.appendNum(attempt);
            crawlDatas.save();
        } catch (IOException e) {
            System.out.printf("[저장 중 에러가 발생했습니다. :: %s]\n", e.getMessage());
        }
    }

    /**
     * 탐색 시작
     */
    public void start() {
        if(waitCss.equals("")) setWaitCss("body");
        ExecutorService executor = Executors.newFixedThreadPool(this.threadCount);
        for(int cnt = 0 ; cnt < this.threadCount ; cnt++) {
            executor.submit(this::run);
        }
    }

    /**
     * 자동 저장을 위한 Attempt, 멀티 스레드를 위해 동기로 처리
     * @return attempt
     */
    private synchronized int getAttempt() {
        return attempt;
    }
    private synchronized void addAttempt() {
        if(++attempt % 100 == 0) save(attempt);
    }

    private void run() {
        ChromeDriver threadDriver = driver.clone();
        threadDriver.init();
        boolean syncWait = false;

        int selfAttempt = 0;
        String threadName = Thread.currentThread().getName();

        do {

            String url = queue.poll();
            if(url == null) {
                if(syncWait) break;
                syncWait = true;
                try {
                    Thread.sleep(10 * 1000);
                } catch (InterruptedException e) {
                    throw new RuntimeException(e);
                }
                continue;
            }
            if(!isTargetDocs(url)) continue;

            addAttempt();
            System.out.printf("[%s-%03d :: Attempt %04d] %s\n", threadName, ++selfAttempt, getAttempt(), url);

            try {
                threadDriver.connect(url);
            } catch (TimeoutException timeout) {
                System.out.printf("[URL %s]에 대한 탐색 중 시간초과 발생\n", url);
            }

            try {
                searcher.search(url.replace(URL_PREFIX, ""), queue, threadDriver.findElement(By.tagName("body")));
            } catch (Exception ex) {
                System.out.printf("===> ! %s ! <====\n", ex.getClass().toString());
                System.out.printf("[Thread-%s][URL %s]에 대한 탐색 중 오류 발생\n", Thread.currentThread().getName(), url);
                for(StackTraceElement stacktrace : ex.getStackTrace()) {
                    System.out.println(stacktrace.toString());
                }
            }

            int[] size = queue.size();
            System.out.printf("현재 Queue size => [PRE] %d [POST] %d\n", size[0], size[1]);

        }while(!queue.isEmpty());

        save(attempt);
        threadDriver.close();
    }
}
