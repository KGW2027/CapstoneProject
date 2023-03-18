package org.example;

import org.openqa.selenium.By;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.io.File;
import java.time.Duration;
import java.util.List;

public class ChromeDriver {

    private ChromeOptions options;
    private WebDriver driver;
    private long timeout;
    private ExpectedCondition waitCondition;

    public ChromeDriver() {
        String DRIVER = "./module/chromedriver_win32/chromedriver.exe";
        System.setProperty("webdriver.chrome.driver", new File(DRIVER).getAbsolutePath());

        options = new ChromeOptions();
        options.addArguments("--disable-popup-blocking");
        options.addArguments("--remote-allow-origins=*");
        options.addArguments("--disable-gpu");
        timeout = 10L;
    }

    public ChromeDriver setTimeout(long time) {
        timeout = time;
        return this;
    }

    public ChromeDriver enableHeadlessMode() {
        options.addArguments("headless");
        return this;
    }

    public ChromeDriver init() {
        driver = new org.openqa.selenium.chrome.ChromeDriver(options);
        return this;
    }

    public ChromeDriver setWait(ExpectedCondition condition) {
        waitCondition = condition;
        return this;
    }

    public void reconnect() {
        driver.close();
        driver = new org.openqa.selenium.chrome.ChromeDriver(options);
    }

    public void connect(String url) throws TimeoutException {
        driver.get(url);
        if(waitCondition != null)
            new WebDriverWait(driver, Duration.ofSeconds(timeout)).until(waitCondition);
    }

    public List<WebElement> findElements(By condition) {
        return driver.findElements(condition);
    }

    public static ExpectedCondition<Boolean> attributeToBeNotEmpty(By locator, String attributeName) {
        return driver -> {
            WebElement element = driver.findElement(locator);
            String attributeValue = element.getAttribute(attributeName);
            return !attributeValue.isEmpty();
        };
    }
}
