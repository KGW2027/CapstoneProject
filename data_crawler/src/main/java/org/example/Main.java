package org.example;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Main {
    private static final String CHAMPIONS = "https://www.leagueoflegends.com/en-us/champions/";
    private static final String STORY = "https://universe-meeps.leagueoflegends.com/v1/en_gb/story/{champ}-color-story/index.json";
    private static final String STORY_ARG = "{champ}";

    public static void main(String[] args) throws Exception {
//        loadChampions();
//        loadStories();
    }

    private static void loadChampions() throws Exception {
        final Pattern champion_name = Pattern.compile("(?<=(en-us/champions/))(.*?)(?=/\">)");

        URL url = new URL(CHAMPIONS);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        if(conn.getResponseCode() == 200) {
            BufferedInputStream bis = new BufferedInputStream(conn.getInputStream());
            int b;
            StringBuilder sb = new StringBuilder();
            while( (b = bis.read()) > 0) {
                sb.append((char) b);
            }

            Matcher matcher = champion_name.matcher(sb);
            List<String> champions = new ArrayList<>();
            while(matcher.find()) {
                champions.add(matcher.group());
            }

            File name_file = new File("./name.txt");
            if(!name_file.exists()) {
                name_file.createNewFile();
            }

            PrintWriter pw = new PrintWriter(new OutputStreamWriter(new FileOutputStream(name_file)));
            for(String s : champions) {
                pw.println(s);
            }
            pw.flush();
            pw.close();
        }
    }

    private static List<String> getChamps() throws Exception {
        File name_file = new File("./name.txt");
        BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(name_file)));
        List<String> list = new ArrayList<>();

        String name;
        while( (name = br.readLine()) != null ) list.add(name);
        br.close();

        return list;
    }

    private static String getHtml(InputStream is) throws Exception {
        StringBuilder sb = new StringBuilder();

        BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8));
        String line;
        while( (line = reader.readLine()) != null) sb.append(line);
        reader.close();

        return sb.toString();
    }

    private static HashSet<String> getLines(String s) {
        HashSet<String> set = new HashSet<>();
        String pattern = "(\\.+)";  // 연속된 모든 온점에 매칭되는 정규식 패턴
        String result = s.replaceAll(pattern, "$1\n").toString();
        String[] split = result.split("\n");
        for(String line : split) {
            if(line.startsWith(" ")) line = line.substring(1);
            set.add(line);
        }
        return set;
    }

    private static void loadStories() throws Exception {
        List<String> champs = getChamps();
        JSONArray all = new JSONArray();
        HashSet<String> titles = new HashSet<>();
        int cnt = 0;
        for(String name : champs) {
            System.out.printf("Champion : %s [ %.2f%%, %d / %d ]\n", name, (100.f * cnt / champs.size()), ++cnt, champs.size());
            Thread.sleep(1 * 1000);
            JSONArray array = getChampionStory(name);
            if(array == null) continue;
            for(Object o : array) {
                JSONObject jo = (JSONObject) o;
                if(jo.containsKey("title")) {
                    String title = (String) jo.get("title");
                    if(titles.contains(title)) continue;
                    titles.add(title);
                }
                all.add(jo);
            }
        }

        File stories = new File("./stories_unlabeled.txt");
        if(!stories.exists()) stories.createNewFile();

        PrintWriter writer = new PrintWriter(new OutputStreamWriter(new FileOutputStream(stories)));

        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        JsonElement ge = JsonParser.parseString(all.toJSONString());
        writer.write(gson.toJson(ge));

        writer.flush();
        writer.close();
    }

    private static JSONObject parseFeatureStory(JSONObject o, String champion) {
        JSONObject featured = (JSONObject) o;

        String name = (String) featured.get("name");
        String title = (String) featured.get("title");
        String type = (String) featured.get("type");

        JSONObject biography = (JSONObject) featured.get("biography");

        String full = (String) biography.get("full");
        String aShort = (String) biography.get("short");
        String quote = (String) biography.get("quote");

        return (JSONObject) makeJson(getLines(full), getLines(aShort), getLines(quote), name, title, type, champion);
    }

    private static JSONArray getChampionStory(String champion) {
        try {
            JSONArray array = new JSONArray();

            URL url = new URL(STORY.replace(STORY_ARG, champion));
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            if (conn.getResponseCode() != 200) return null;

            String html = getHtml(conn.getInputStream()).replaceAll("\\<[^>]*>", "");
            JSONObject json = (JSONObject) (new JSONParser()).parse(html);
            JSONObject story = (JSONObject) json.get("story");

            JSONObject section = (JSONObject) ((JSONArray) story.get("story-sections")).get(0);

            JSONObject subsect = (JSONObject) ((JSONArray) section.get("story-subsections")).get(0);
            String content1 = (String) subsect.get("content");
            array.add(makeJson(getLines(content1), champion));

            JSONArray features = (JSONArray) section.get("featured-champions");
            for(Object o : features) {
                array.add(parseFeatureStory((JSONObject) o, champion));
            }

            return array;
        }catch(Exception ex) {
            System.out.printf("Champion %s에서 에러가 발생해 스킵되었습니다.\n", champion);
            return null;
        }
    }

    private static String parseHashSet(HashSet<String> story) {
        String context = "";
        for(String line : story)
            context = context.concat(" ").concat(line);
        return context;
    }

    private static Object makeJson(HashSet<String> story, String champion) {
        JSONObject object = new JSONObject();
        object.put("type", "champion");
        object.put("owner", champion);
        object.put("context", parseHashSet(story));
        return object;
    }

    private static Object makeJson(HashSet<String> biography, HashSet<String> shot, HashSet<String> quote, String name, String title, String type, String ownerChampion) {
        JSONObject object = new JSONObject();
        object.put("type", "biography");
        object.put("owner", ownerChampion);
        object.put("context", parseHashSet(biography));
        object.put("short", parseHashSet(shot));
        object.put("quote", parseHashSet(quote));
        object.put("name", name);
        object.put("title", title);
        object.put("biography-type", type);
        return object;
    }
}