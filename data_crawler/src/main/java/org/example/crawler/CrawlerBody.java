package org.example.crawler;

import org.example.ChromeDriver;
import org.json.simple.JSONObject;
import org.openqa.selenium.By;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
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
    private final CrawlingDatas crawlingDatas;
    private final CrawlingQueue queue;
    private final CrawlingSearcher searcher;
    private final List<String> blacklists;
    private boolean cssSetted;
    private int threadCount;

    private final HashMap<Thread, ChromeDriver> claimDrivers;
    private final HashMap<Thread, List<String>> threadURLs;
    private int searchEnd;

    private final ChromeDriver driver;

    public CrawlerBody(CrawlingQueue queue, CrawlingSearcher searcher) {
        this.crawlingDatas = new CrawlingDatas(queue.getName());
        this.URL_PREFIX = queue.getPrefix().toLowerCase();
        this.queue = queue;
        this.searcher = searcher.setBody(this);
        this.cssSetted = false;
        this.blacklists = new ArrayList<>();
        this.threadCount = 1;
        this.searchEnd = 0;
        claimDrivers = new HashMap<>();
        threadURLs = new HashMap<>();

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
        cssSetted = true;
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
    public CrawlerBody addBlacklist(String... blacklist) {
        for(String black : blacklist)
            this.blacklists.add(black.toLowerCase());
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
        crawlingDatas.put(docName, data);
    }

    public synchronized void addCrawlingData(String docName, JSONObject data) {
        crawlingDatas.put(docName, data);
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
            crawlingDatas.clearName();
            crawlingDatas.appendDate();
            crawlingDatas.appendNum(attempt);
            crawlingDatas.save();
        } catch (IOException e) {
            System.out.printf("[저장 중 에러가 발생했습니다. :: %s]\n", e.getMessage());
        }
    }

    private synchronized void end() {
        printMessage(String.format("Occur end %d", this.searchEnd));
        if(++this.searchEnd >= this.threadCount)
            save(0);
    }

    /**
     * 탐색 시작
     */
    public void start() {
        if(!cssSetted) setWaitCss("body");
        ExecutorService executor = Executors.newFixedThreadPool(this.threadCount);
        for(int cnt = 0 ; cnt < this.threadCount ; cnt++) {
            executor.submit(this::run);
            try {
                Thread.sleep(100);
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        }
    }

    /**
     * 현재 스레드의 드라이버 반환
     */
    public ChromeDriver getDriver() {
        return claimDrivers.get(Thread.currentThread());
    }

    public void printMessage(String message) {
        System.out.printf("[%s] %s\n", Thread.currentThread().getName().replace("pool-1-", ""), message);
    }

    public synchronized void updateMessage(String newUrl) {
        StringBuilder sb = new StringBuilder();
        String messageFormat = "%s (%03d) :: %s\n";
        for(Thread thread : claimDrivers.keySet()) {
            if(!threadURLs.containsKey(thread)) threadURLs.put(thread, new ArrayList<>());
            if(thread == Thread.currentThread()) threadURLs.get(thread).add(newUrl);

            String name = thread.getName().replace("pool-1-", "");
            int size = threadURLs.get(thread).size();
            String url = size > 0
                    ? threadURLs.get(thread).get(size-1)
                    : "None";
            sb.append(String.format(messageFormat, name, size, url));
        }
        System.out.printf("[Current Status]\n%s\n", sb);
    }

    private void run() {
        ChromeDriver threadDriver = driver.clone();
        threadDriver.init();
        claimDrivers.put(Thread.currentThread(), threadDriver);
        int wait = 0;

        do {
            String url = queue.poll();

            if(url == null) {
                if(++wait >= 4) break;
                try {
                    Thread.sleep(10 * 1000);
                } catch (InterruptedException e) {
                    throw new RuntimeException(e);
                }
                printMessage("[Sync Wait]");
                continue;
            }
            if(!isTargetDocs(url)) continue;

            updateMessage(url);

            try {
                threadDriver.connect(url);
            } catch (TimeoutException timeout) {
                printMessage(String.format("URL [%s] 탐색 중 Timeout", url));
                continue;
            }

            try {
                searcher.search(url.replace(URL_PREFIX, ""), queue, threadDriver.findElement(By.tagName("body")));
            } catch (Exception ex) {
                printMessage(String.format("===> ! %s ! <====\n", ex.getClass().toString()));
                printMessage(String.format("URL [%s] 탐색 중 Exception\n", url));
                for(StackTraceElement stacktrace : ex.getStackTrace()) {
                    printMessage(stacktrace.toString());
                }
                continue;
            }

            int[] size = queue.size();
            System.out.printf("현재 Queue size => [PRE] %d [POST] %d\n", size[0], size[1]);

        }while(!queue.isEmpty());

        printMessage("Out of Loop");
        end();
        threadDriver.close();
    }
}
