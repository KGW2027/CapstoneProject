package org.example.translator;

public enum Language {
    KOREAN("ko"),
    ENGLISH("en");

    String langKey;

    Language(String key) {
        langKey = key;
    }

    public String getLangKey() {
        return langKey;
    }

}
