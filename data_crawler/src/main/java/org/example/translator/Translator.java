package org.example.translator;

import org.example.translator.processors.FandomParser;
import org.json.simple.parser.ParseException;

import java.io.IOException;


public class Translator {

    public static void main(String[] args) throws IOException, ParseException {
        TranslatorMachine machine = new TranslatorMachine(TranslatorAPIs.DEEPL)
                .setLanguage(Language.ENGLISH, Language.KOREAN)
                ;

        new FandomParser(machine).process(null);

    }
}
