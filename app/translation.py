"""
Translation utilities with persistent database caching.
First translation is slow (Google Translate), all subsequent are instant (from DB).
"""
import hashlib
from deep_translator import GoogleTranslator
from django.core.cache import cache


def get_text_hash(text):
    """Generate MD5 hash for text to use as cache key."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def translate_text(text, target_lang='uk'):
    """
    Translates text to the target language.
    Uses: 1) Memory cache (fastest) -> 2) Database cache -> 3) Google Translate (slowest)
    """
    if not text or target_lang == 'en':
        return text

    text_hash = get_text_hash(text)
    
    # 1. Check memory cache first (fastest)
    cache_key = f'trans_{target_lang}_{text_hash}'
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # 2. Check database cache (fast)
    from .models import TranslationCache
    try:
        db_cached = TranslationCache.objects.filter(
            source_text_hash=text_hash,
            target_lang=target_lang
        ).first()
        
        if db_cached:
            # Also set in memory cache for even faster next access
            cache.set(cache_key, db_cached.translated_text, 86400)
            return db_cached.translated_text
    except Exception:
        pass  # DB not ready yet, continue to translate
    
    # 3. Translate via Google (slow, but only happens once per text)
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated = translator.translate(text)
        
        if translated:
            # Save to database (permanent)
            try:
                TranslationCache.objects.update_or_create(
                    source_text_hash=text_hash,
                    target_lang=target_lang,
                    defaults={'translated_text': translated}
                )
            except Exception:
                pass  # DB save failed, still return translation
            
            # Save to memory cache (temporary, for speed)
            cache.set(cache_key, translated, 86400)
            return translated
    except Exception as e:
        print(f"Translation error: {e}")
    
    return text


def translate_text_batch(texts, target_lang='uk'):
    """
    Batch translate a list of texts.
    Optimized: checks DB cache first, only translates missing items.
    """
    if not texts or target_lang == 'en':
        return texts
    
    from .models import TranslationCache
    
    results = {}
    to_translate = []
    to_translate_indices = []
    
    # 1. Check caches for all texts
    for i, text in enumerate(texts):
        if not text:
            results[i] = text
            continue
            
        text_hash = get_text_hash(text)
        cache_key = f'trans_{target_lang}_{text_hash}'
        
        # Check memory cache
        cached = cache.get(cache_key)
        if cached:
            results[i] = cached
            continue
        
        # Check database cache
        try:
            db_cached = TranslationCache.objects.filter(
                source_text_hash=text_hash,
                target_lang=target_lang
            ).first()
            
            if db_cached:
                cache.set(cache_key, db_cached.translated_text, 86400)
                results[i] = db_cached.translated_text
                continue
        except Exception:
            pass
        
        # Need to translate this one
        to_translate.append((i, text, text_hash))
    
    # 2. Batch translate missing items
    if to_translate:
        try:
            texts_to_trans = [t[1] for t in to_translate]
            translator = GoogleTranslator(source='auto', target=target_lang)
            
            # Translate in small batches to avoid timeouts
            translated = translator.translate_batch(texts_to_trans)
            
            # Save results
            for idx, (orig_idx, orig_text, text_hash) in enumerate(to_translate):
                if idx < len(translated) and translated[idx]:
                    trans_text = translated[idx]
                    results[orig_idx] = trans_text
                    
                    # Save to database
                    try:
                        TranslationCache.objects.update_or_create(
                            source_text_hash=text_hash,
                            target_lang=target_lang,
                            defaults={'translated_text': trans_text}
                        )
                    except Exception:
                        pass
                    
                    # Save to memory cache
                    cache_key = f'trans_{target_lang}_{text_hash}'
                    cache.set(cache_key, trans_text, 86400)
                else:
                    results[orig_idx] = orig_text
                    
        except Exception as e:
            print(f"Batch translation error: {e}")
            # Fallback: return originals for failed translations
            for orig_idx, orig_text, _ in to_translate:
                if orig_idx not in results:
                    results[orig_idx] = orig_text
    
    # 3. Reconstruct ordered list
    return [results.get(i, texts[i]) for i in range(len(texts))]


def translate_anime_data(anime_data, target_lang='uk'):
    """
    Translates common fields in the anime data dictionary.
    """
    if not anime_data or target_lang != 'uk':
        return anime_data

    # Fields to translate
    anime_data['synopsis'] = translate_text(anime_data.get('synopsis'), target_lang)
    anime_data['status'] = translate_text(anime_data.get('status'), target_lang)
    anime_data['type'] = translate_text(anime_data.get('type'), target_lang)
    anime_data['source'] = translate_text(anime_data.get('source'), target_lang)

    # Translate Genres
    if 'genres' in anime_data:
        for genre in anime_data['genres']:
            genre['name'] = translate_text(genre.get('name'), target_lang)
            
    return anime_data
