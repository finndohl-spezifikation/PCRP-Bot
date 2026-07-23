package de.pcrp.bot.common;

/**
 * Wortfilter für vulgäre Kraftausdrücke (Deutsch + Englisch).
 * Nachrichten mit Treffern werden sofort gelöscht.
 * Leetspeak-Normalisierung ist integriert (z.B. "f1ck" → "fick").
 */
public final class WordFilter {

    private static final String[] BANNED_WORDS = {
        // Deutsch
        "hurensohn", "hurentochter", "hure", "nutte", "fotze", "wichser",
        "wixer", "wixxer", "schlampe", "missgeburt", "bastard", "arschloch",
        "drecksau", "dreckskerl", "spast", "spasti", "mongo", "behindert",
        "fick dich", "fickt euch", "verfickt", "ficker", "kanake", "untermensch",
        // Englisch
        "fuck", "fucking", "fucker", "motherfucker", "bitch", "asshole",
        "cunt", "slut", "whore", "dickhead", "retard", "faggot", "nigger",
        "nigga", "cocksucker", "son of a bitch",
    };

    private WordFilter() {}

    /** Prüft, ob der Text einen vulgären Kraftausdruck enthält. */
    public static boolean containsBannedWord(String content) {
        return getMatchedWord(content) != null;
    }

    /**
     * Gibt das erste gefundene verbotene Wort zurück, oder null wenn keines gefunden wurde.
     * Wird vom Log-System genutzt, um den gefundenen Begriff zu protokollieren.
     */
    public static String getMatchedWord(String content) {
        if (content == null || content.isBlank()) return null;
        String normalized = normalize(content);
        for (String word : BANNED_WORDS) {
            if (normalized.contains(word)) return word;
        }
        return null;
    }

    /** Kleinbuchstaben + einfache Leetspeak-Umschreibungen auflösen. */
    private static String normalize(String input) {
        StringBuilder sb = new StringBuilder(input.length());
        for (char c : input.toLowerCase().toCharArray()) {
            sb.append(switch (c) {
                case '0' -> 'o';
                case '1' -> 'i';
                case '3' -> 'e';
                case '4' -> 'a';
                case '5' -> 's';
                case '7' -> 't';
                case '@' -> 'a';
                case '$' -> 's';
                default  -> c;
            });
        }
        return sb.toString();
    }
}
