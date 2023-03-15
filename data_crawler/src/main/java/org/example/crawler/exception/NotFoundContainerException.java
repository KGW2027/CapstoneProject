package org.example.crawler.exception;

public class NotFoundContainerException extends Exception {
    public NotFoundContainerException(String docName) {
        System.out.printf("[Document %s] Container를 발견하지 못해 스킵됩니다.\n", docName);
    }
}
