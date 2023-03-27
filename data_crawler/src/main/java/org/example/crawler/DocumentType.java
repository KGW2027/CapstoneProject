package org.example.crawler;

public enum DocumentType {
    Category("Category"),
    Document(""),
    File("File"),
    Unknown("Unknown");

    String prefix;

    DocumentType(String prefix) {
        this.prefix = prefix;
    }

    public static DocumentType getType(String url){
        int lastSeperator = url.lastIndexOf('/');
        url = url.substring(lastSeperator+1);
        System.out.println(url);
        if(url.indexOf(':') < 0) return Document;

        for(DocumentType dt : values()) {
            if(dt == Document) continue;
            if(url.startsWith(dt.prefix)) return dt;
        }
        return Unknown;
    }
}
