package org.example.crawler;


import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class Categories {

    private class Category {
        List<String> parents;
        boolean isLore;

        Category() {
            parents = new ArrayList<>();
            isLore = true;
        }
    }

    private static Categories instance;
    public static Categories getInstance() {
        return (instance == null) ? (instance = new Categories()) : instance;
    }

    HashMap<String, Category> categoryMap;

    private Categories() {
        categoryMap = new HashMap<>();
    }

    public boolean addCategory(String name, String... parent) {
        if(!categoryMap.containsKey(name)) categoryMap.put(name, new Category());
        for(String p : parent) categoryMap.get(name).parents.add(p.toLowerCase().replace(" ", ""));
        return false;
    }
}
