package org.example.translator;

import org.json.simple.JSONArray;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.*;
import java.util.HashSet;

public abstract class CrawlDataProcessor {

    public abstract void process(HashSet<String> texts) throws IOException, ParseException;
    public abstract String getDirectoryName();
    public abstract String getSrcPath();

    protected JSONArray readSource() throws IOException, ParseException {
        String target = getSrcPath();
        BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(target)));

        StringBuilder read = new StringBuilder();
        String line;
        while( (line = br.readLine()) != null) read.append(line);
        br.close();
        return (JSONArray) new JSONParser().parse(read.toString());
    }
}
