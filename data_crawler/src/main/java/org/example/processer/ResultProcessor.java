package org.example.processer;

//import com.google.gson.Gson;
//import com.google.gson.GsonBuilder;
//import com.google.gson.JsonElement;
//import com.google.gson.JsonParser;
//import org.json.simple.JSONArray;
//import org.json.simple.JSONObject;
//import org.json.simple.parser.JSONParser;
//import org.json.simple.parser.ParseException;
//
//import java.io.*;
//import java.util.*;
//import java.util.regex.Matcher;
//import java.util.regex.Pattern;
//
public class ResultProcessor {

//
//    private static void fandomPostProcess() throws IOException, ParseException {
//
//        StringBuilder sb = new StringBuilder();
//        BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream("./data/processing/fandom-en2.json")));
//        String line;
//
//        HashMap<String, Integer> appear_map = new HashMap<>();
//        Pattern ptn = Pattern.compile("(development|roadmap|gameplay|release|version|update|rework|report|support|seasons|event|strategy|tricks|only|visual|upgrade|note)");
//        Pattern otherGame = Pattern.compile("(LoR|TFT)");
//
//        while((line=br.readLine()) != null) sb.append(line);
//        JSONArray ja = (JSONArray) (new JSONParser().parse(sb.toString()));
//        JSONArray newArray = new JSONArray();
//        for(Object o : ja) {
//            JSONObject jo = (JSONObject) o;
//
//            String title = jo.get("title").toString();
//            Matcher titleMatcher = otherGame.matcher(title);
//            if(titleMatcher.find()) {
//                System.out.printf("%s는 게임과 관련된 내용으로 판단되어 삭제됩니다. [ matched : %s ]\n", title, titleMatcher.group());
//                continue;
//            }
//
//            JSONArray newInner = new JSONArray();
//            int count = 0;
//            JSONArray iter = (JSONArray) ((JSONObject) jo.get("data")).get("inner");
//            if(iter != null) {
//                for (Object o2 : iter) {
//                    JSONObject jo2 = (JSONObject) o2;
//                    if (jo2.keySet().size() == 0) continue;
//                    List<String> removes = new ArrayList<>();
//                    for (Object k : jo2.keySet()) {
//                        String ks = k.toString();
//                        if (ptn.matcher(ks.toLowerCase()).find()) {
//                            removes.add(ks);
//                            continue;
//                        }
//
//                        appear_map.put(ks, appear_map.getOrDefault(ks, 0) + 1);
//                    }
//                    for (String rem : removes) jo2.remove(rem);
//
//                    newInner.add(o2);
//                    count += jo2.size();
//                }
//            }
//
//            JSONObject data = (JSONObject) jo.get("data");
//
//            if(count == 0)
//                data.remove("inner");
//            else
//                data.put("inner", newInner);
//
//            if(data.keySet().contains("quotes") && ((JSONArray) data.get("quotes")).size() == 0)
//                data.remove("quotes");
//
//            if(jo.size() == 0)
//                continue;
//            newArray.add(jo);
//        }
//
//        for(String k : appear_map.keySet()) System.out.printf("%s : %,3d\n", k, appear_map.get(k));
//        System.out.printf("Keys : %,3d\n", appear_map.size());
//
//
//        try {
//            File output = new File("./data/processing/fandom-en2-process.json");
//            if(!output.exists()) output.createNewFile();
//
//            BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(output)));
//            Gson gson = new GsonBuilder().setPrettyPrinting().create();
//            JsonElement ge = JsonParser.parseString(newArray.toJSONString());
//            writer.write(gson.toJson(ge));
//            writer.flush();
//            writer.close();
//        } catch (IOException e) {
//            throw new RuntimeException(e);
//        }
//    }
//
//
//    public static void main(String[] args) throws IOException, ParseException {
////        new ResultProcessor("./data/processing/fandom-en.json")
////                .process();
////        new ResultProcessor("./data/processing/univ-en.json")
////                .process();
////        new ResultProcessor("./data/processing/univ-ko.json")
////                .process();
//        fandomPostProcess(); // File name : ./data/processing/fandom-en2.json
//        new ResultProcessor("./data/processing/fandom-en2-process.json")
//                .process();
//    }
//
//
//    private JSONArray array;
//    private File output;
//    private JSONObject properMap;
//
//    private String preprocess(String line) {
//        return line.replace("“", "\"")
//                .replace("”", "\"")
//                .replace("’", "'")
//                .replace("‘", "'")
//                .replace("…", "...")
//                .replace("—", " ")
//                .replace("–", "")
//                .replace("ø", "o")
//                .replace("♥", "love")
//                .replace("á", "a")
//                .replace("ä", "a")
//                .replace("é", "e")
//                .replace("í", "i")
//                .replace("ö", "o")
//                .replace("ü", "u")
//                .replace("°", " degrees")
//                .replace("·", ",")
//                .replace("「", "\"")
//                .replace("」", "\"")
//                .replace("(bug)", "")
//                .replace("(TBA)", "")
//                .replaceAll("\\[.*?\\]", "")
//                .replaceAll("\\(.*?\\)", "")
//                .replaceAll("^([0-9]+\\n )", "")
//                .replaceAll(" {2,}", " ")
//                ;
//    }
//
//    private ResultProcessor(String path) throws IOException, ParseException {
//
//        File properFile = new File("./data/propermap.json");
//        BufferedReader propReader = new BufferedReader(new InputStreamReader(new FileInputStream(properFile)));
//        String line;
//        StringBuilder builder = new StringBuilder();
//        while ((line = propReader.readLine()) != null) builder.append(line);
//        properMap = (JSONObject) new JSONParser().parse(builder.toString());
//
//        File file = new File(path);
//        BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(file)));
//        builder.setLength(0);
//
//        while ((line = reader.readLine()) != null) builder.append(line);
//        array = (JSONArray) new JSONParser().parse(builder.toString());
//
//        output = new File(path.replace(".json", "-process.json"));
//        if (!output.exists()) output.createNewFile();
//    }
//
//    private HashMap<String, List<String>> sentences = new HashMap<>();
//    private final String seperator = "->";
//
//    private void processData(Object data, String parent, String newPath, boolean parentIsArray) {
//        String path = String.format("%s%s%s", parent, seperator, newPath);
//        if(data instanceof String) {
//            String key = parentIsArray ? parent : path;
//            if(!sentences.containsKey(key))
//                sentences.put(key, new ArrayList<>());
//            String before = data.toString();
//            String after = preprocess(before).trim();
//            sentences.get(key).add(after);
//        } else if (data instanceof JSONObject) {
//            processObject((JSONObject) data, path);
//        } else if (data instanceof JSONArray) {
//            processArray((JSONArray) data, path);
//        } else {
//            System.out.printf("UNKNOWN DATA TYPE : %s\n", data.toString());
//        }
//    }
//
//    private void processArray(JSONArray data, String path) {
//        for(int i = 0 ; i < data.size() ; i++) {
//            processData(data.get(i), path, String.valueOf(i), true);
//        }
//    }
//
//    private void processObject(JSONObject data, String path) {
//        for(Object k : data.keySet()) {
//            String key = k.toString();
//            processData(data.get(key), path, key, false);
//        }
//    }
//
//    private void update(String path, List<String> list) {
//        Object newData;
//        if(list.size() == 1)
//            newData = list.get(0);
//        else {
//            newData = new JSONArray();
//            for (String str : list) ((JSONArray)newData).add(str);
//        }
//
//        String[] paths = path.split(seperator);
//        Object o = array.get(Integer.parseInt(paths[0]));
//        for(int depth = 1 ; depth < paths.length-1 ; depth++) {
//            if(o instanceof JSONArray) {
//                o = ((JSONArray)o).get(Integer.parseInt(paths[depth]));
//            } else if(o instanceof JSONObject){
//                o = ((JSONObject) o).get(paths[depth]);
//            } else {
//                assert true;
//            }
//        }
//
//        if(o instanceof JSONArray)
//            ((JSONArray) o).set(Integer.parseInt(paths[paths.length-1]), newData);
//        else if(o instanceof JSONObject)
//            ((JSONObject) o).put(paths[paths.length-1], newData);
//    }
//
//    private void process() {
//
//        for(int idx = 0 ; idx < array.size() ; idx++) {
//            processData(((JSONObject) array.get(idx)).get("data"), String.valueOf(idx), "data", true);
//        }
//
//        for(String key : sentences.keySet()) {
//            if(sentences.get(key).size() == 0) continue;
//            update(key, sentences.get(key));
//        }
//
//        try {
//            BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(output)));
//            Gson gson = new GsonBuilder().setPrettyPrinting().create();
//            JsonElement ge = JsonParser.parseString(array.toJSONString());
//            writer.write(gson.toJson(ge));
//            writer.flush();
//            writer.close();
//        } catch (IOException e) {
//            throw new RuntimeException(e);
//        }
//    }
//
}
