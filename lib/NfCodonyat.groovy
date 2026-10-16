/**
 * Path helpers for local and object-store (s3://, gs://, az://) URIs.
 * Object stores have prefixes, not directories: checkIfExists / exists()
 * on a prefix is unreliable, so callers skip those checks for remote URIs.
 */
class NfCodonyat {

    static boolean isRemoteUri(def p) {
        if (p == null) {
            return false
        }
        def s = p.toString()
        return s.contains('://')
    }

    /** Directory / prefix URI with a trailing slash for remote paths. */
    static String dirUri(def p) {
        def s = p.toString().replaceAll(/\/+$/, '')
        return isRemoteUri(s) ? "${s}/" : s
    }

    /** Directory URI without a trailing slash (for joining child names). */
    static String dirRoot(def p) {
        return p.toString().replaceAll(/\/+$/, '')
    }
}
