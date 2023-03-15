package org.example.crawler.fandomen;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class FandomEnCategories {

    enum ValidateLore {
        Unchecked,
        Validate,
        NotValidate;
    }

    private class Category {
        List<Integer> parents;
        ValidateLore isLore;

        Category() {
            parents = new ArrayList<>();
            isLore = ValidateLore.Unchecked;
        }

        ValidateLore validLore() {
            if(isLore == ValidateLore.NotValidate) return ValidateLore.NotValidate;
            if(isLore == ValidateLore.Validate) return ValidateLore.Validate;

            for(int parent : parents) {
                isLore = getInstance().categories.get(parent).validLore();
                if(isLore == ValidateLore.Validate) break;
            }
            return isLore;
        }
    }

    private static FandomEnCategories instance;
    public static FandomEnCategories getInstance() {
        return (instance == null) ? (instance = new FandomEnCategories()) : instance;
    }

    List<Category> categories;
    HashMap<String, Integer> categoryMap;

    private FandomEnCategories() {
        categoryMap = new HashMap<>();
        categories = new ArrayList<>();

        categoryMap.put("lore", 1);

        Category lore = new Category();
        lore.isLore = ValidateLore.Validate;
        categories.add(new Category());
        categories.add(lore);
    }

    private String normalizeName(String name) {
        return name.toLowerCase().replace(" ", "");
    }

    private int newCategory(String name) {
        if(categoryMap.containsKey(name)) return categoryMap.get(name);
        int size = categories.size();
        categoryMap.put(name, size);
        categories.add(new Category());
        return size;
    }

    public boolean addCategory(String name, String... parents) {
        int self = newCategory(normalizeName(name));
        for(String parent : parents) {
            parent = normalizeName(parent);
            if(!categoryMap.containsKey(parent)) continue;
            categories.get(self).parents.add(categoryMap.get(parent));
        }

        return categories.get(self).validLore() == ValidateLore.Validate;
    }

    public boolean validLore(String... parents) {
        for(String parent : parents) {
            parent = normalizeName(parent);
            if(!categoryMap.containsKey(parent)) continue;
            if(categories.get(categoryMap.get(parent)).validLore() == ValidateLore.Validate) return true;
        }
        return false;
    }
}
