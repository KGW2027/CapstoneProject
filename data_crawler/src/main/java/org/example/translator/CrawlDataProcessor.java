package org.example.translator;

import org.json.simple.parser.ParseException;

import java.io.IOException;
import java.util.HashSet;

public abstract class CrawlDataProcessor {

    public abstract void process(HashSet<String> texts) throws IOException, ParseException;
    public abstract String getDirectoryName();
}
