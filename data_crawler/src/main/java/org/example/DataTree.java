package org.example;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.regex.Pattern;

public class DataTree {

    private HashMap<String, List<String>> dataMap;
    private List<String> nullPaths;
    private JSONArray baseArray;
    private final String seperator = "->";

    public DataTree(JSONArray array) {
        dataMap = new HashMap<>();
        nullPaths = new ArrayList<>();
        baseArray = array;

        for(int idx = 0 ; idx < array.size() ; idx++) {
            processData(array.get(idx), null, String.valueOf(idx), true);
        }
    }


    private void processData(Object data, String parent, String newPath, boolean parentIsArray) {
        String path = (parent == null) ? newPath : String.format("%s%s%s", parent, seperator, newPath);
        Pattern except = Pattern.compile("^[0-9]+->title");
        if(except.matcher(path).find()) return;

        if(data instanceof String) {
            String key = parentIsArray ? parent : path;
            if(!dataMap.containsKey(key))
                dataMap.put(key, new ArrayList<>());
            dataMap.get(key).add(data.toString());
        } else if (data instanceof JSONObject) {
            processObject((JSONObject) data, path);
        } else if (data instanceof JSONArray) {
            processArray((JSONArray) data, path);
        } else {
            nullPaths.add(path);
        }
    }

    private void processArray(JSONArray data, String path) {
        for(int i = 0 ; i < data.size() ; i++) {
            processData(data.get(i), path, String.valueOf(i), true);
        }
    }

    private void processObject(JSONObject data, String path) {
        for(Object k : data.keySet()) {
            String key = k.toString();
            processData(data.get(key), path, key, false);
        }
    }

    public Iterator<String> getKeys() {
        return dataMap.keySet().iterator();
    }

    public List<String> getValue(String key) {
        return dataMap.get(key);
    }

    public void update(String key, List<String> updateList) {
        dataMap.put(key, updateList);
    }

    public JSONArray apply() {
        for(String key : dataMap.keySet())
            applyToBase(key, dataMap.get(key));
        for(String path : nullPaths)
            checksNull(path);

        return baseArray;
    }

    public void remove(String path) {
        String[] paths = path.split(seperator);
        String key = paths[paths.length-1];
        Object o = baseArray.get(Integer.parseInt(paths[0]));
        if(o instanceof JSONArray)
            ((JSONArray) o).remove(Integer.parseInt(key));
        else if(o instanceof JSONObject)
            ((JSONObject) o).remove(key);
    }

    private Object getPathObject(String path) {
        String[] paths = path.split(seperator);
        Object o = baseArray.get(Integer.parseInt(paths[0]));
        for(int depth = 1 ; depth < paths.length-1 ; depth++) {
            if(o instanceof JSONArray) {
                o = ((JSONArray)o).get(Integer.parseInt(paths[depth]));
            } else if(o instanceof JSONObject){
                o = ((JSONObject) o).get(paths[depth]);
            } else {
                assert true;
            }
        }
        return o;
    }

    private void checksNull(String path) {
        Object o = getPathObject(path);
        if(o instanceof JSONArray) {
            JSONArray ja = (JSONArray) o;
            ja.remove(null);

            if(ja.size() == 0) {
                remove(path);
            }
        }

    }

    private void applyToBase(String path, List<String> list) {
        Object newData;
        if(list.size() == 0) return;

        if(list.size() == 1)
            newData = list.get(0);
        else {
            newData = new JSONArray();
            for (String str : list) ((JSONArray)newData).add(str);
        }

        String[] paths = path.split(seperator);
        String key = paths[paths.length-1];
        Object o = getPathObject(path);

        if(o instanceof JSONArray)
            ((JSONArray) o).set(Integer.parseInt(key), newData);
        else if(o instanceof JSONObject)
            ((JSONObject) o).put(key, newData);
    }

    public int getSize() {
        return dataMap.size();
    }
}
