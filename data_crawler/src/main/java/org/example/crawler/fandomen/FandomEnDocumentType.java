package org.example.crawler.fandomen;

public enum FandomEnDocumentType {
    Category("Category", false),
    Document("", true),
    Template("Template", false),
    File("File", false),
    Unknown("Unknown", true);

    String prefix;
    boolean isDocument;

    FandomEnDocumentType(String prefix, boolean isDocs) {
        this.prefix = prefix;
        this.isDocument = isDocs;
    }

    public static FandomEnDocumentType getType(String url){
        int lastSeperator = url.lastIndexOf('/');
        url = url.substring(lastSeperator+1);
        if(url.indexOf(':') < 0) return Document;

        for(FandomEnDocumentType dt : values()) {
            if(dt == Document) continue;
            if(url.startsWith(dt.prefix)) return dt;
        }
        return Unknown;
    }
}
