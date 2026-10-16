/**
 * Path helpers for local and object-store (s3://, gs://, az://) URIs.
 *
 * Nextflow's file('s3://bucket/key') stringifies as '/bucket/key' (no scheme).
 * Always prefer toUriString() or the original URI string so remote paths are
 * not treated as local files.
 */
class NfCodonyat {

    /** s3://… or the URI of a Nextflow file() object (not Path.toString()). */
    static String uriString(def p) {
        if (p == null) {
            return ''
        }
        try {
            if (p.metaClass.respondsTo(p, 'toUriString')) {
                def u = p.toUriString()
                if (u) {
                    return u.toString()
                }
            }
        } catch (Exception ignored) {
        }
        return p.toString()
    }

    static boolean isRemoteUri(def p) {
        if (p == null) {
            return false
        }
        def s = uriString(p)
        if (s ==~ /^(s3|s3n|s3a|gs|az|http|https):\/\/.*/) {
            return true
        }
        try {
            if (p.metaClass.respondsTo(p, 'getScheme')) {
                def sch = p.getScheme()?.toString()?.toLowerCase()
                if (sch) {
                    return sch in ['s3', 's3n', 's3a', 'gs', 'az', 'http', 'https']
                }
            }
        } catch (Exception ignored) {
        }
        return s.contains('://') && !s.startsWith('file:')
    }

    /** Directory / prefix URI with a trailing slash for remote paths. */
    static String dirUri(def p) {
        def s = uriString(p).replaceAll(/\/+$/, '')
        return isRemoteUri(p) || isRemoteUri(s) ? "${s}/" : s
    }

    /** Directory URI without a trailing slash (for joining child names). */
    static String dirRoot(def p) {
        return uriString(p).replaceAll(/\/+$/, '')
    }
}
