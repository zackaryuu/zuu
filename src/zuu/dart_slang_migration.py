from collections.abc import Generator
from functools import cache, lru_cache
import os
import re
from typing import TypedDict
import typing
from .simple_dict import deep_set


from zuu import dart


@lru_cache(maxsize=100)
def _cache_dart_file_content(path: str) -> str:
    """
    Cache and return the content of a Dart file.

    Args:
        path: Absolute path to the Dart file

    Returns:
        String content of the file
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def gather_intl_translation_usage(folder: str, prefix: str = "AppLocalizations"):
    """
    Scan Dart files in a folder to extract AppLocalizations usage patterns.

    Searches for patterns like {prefix}.of(context)!.{variable_name}
    and collects all the translation keys used in each file.

    Args:
        folder: Root folder path to recursively scan for .dart files

    Returns:
        Dictionary mapping filenames to lists of translation keys found in each file

    Example:
        {
            "login_screen.dart": ["loginButtonLabel", "passwordHintText"],
            "home_screen.dart": ["welcomeMessage", "logoutLabel"]
        }
    """

    per_file_matches = {}

    for root, dirs, files in os.walk(folder):
        for filename in files:
            if not filename.endswith(".dart"):
                continue
            content = _cache_dart_file_content(os.path.join(root, filename))

            # extract all phrases that is wrapped in the following format
            # {prefix}.of(context)!.{var}

            pattern = rf"{prefix}\.of\(context\)!\.(\w+)"
            matches = re.findall(pattern, content)

            if matches:
                per_file_matches[
                    os.path.relpath(os.path.join(root, filename), folder)
                ] = matches

    return per_file_matches


def normalize_to_nested_map(
    translation_usage: dict,
    maxlv: int = 3,
    wordsToRemove: list = None,
    customMatchFunctions: list = None,
    strict_word_splitting: bool = True,
) -> dict:
    """
    Convert flat translation keys into dot notation keys based on screen names and common patterns.

    Args:
        translation_usage: Dict mapping dart file paths to lists of translation keys
        maxlv: Maximum nesting level to create by finding common groups
        wordsToRemove: List of words to remove from keys (case insensitive)
        customMatchFunctions: List of functions to apply custom transformations
        strict_word_splitting: If True, only treat sequences of 4+ chars as separate words (preserves abbreviations like 'Btn').
                              If False, use aggressive splitting that treats any capitalized sequence as a word.

    Returns:
        Dictionary with dot notation keys like 'activitySuggestionScreen.activities.selectedLabel'
    """
    from .nested_dict import compute_nested, flatten_dict
    
    if not translation_usage:
        return {}
    
    # Collect all unique keys from all files
    all_keys = []
    for keys in translation_usage.values():
        all_keys.extend(keys)
    
    # Remove duplicates while preserving order
    unique_keys = list(dict.fromkeys(all_keys))
    
    if not unique_keys:
        return {}
    
    # Create screen name mapping: each key maps to screen name based on which file it appears in
    screen_mapping = {}
    for file_path, keys in translation_usage.items():
        if not keys:
            continue
            
        # Extract screen name from file path
        # e.g., "activity_suggestion_screen.dart" -> "activitySuggestionScreen"
        filename = os.path.basename(file_path).replace(".dart", "")
        screen_name = _snake_to_camel_case(filename)
        
        # Map each key in this file to this screen name
        for key in keys:
            screen_mapping[key] = screen_name
    
    # Create supplementary dictionaries for compute_nested
    supplementary_dicts = []
    
    # Screen mapping is the primary grouping mechanism
    screen_dict = {}
    for key in unique_keys:
        if key in screen_mapping:
            screen_dict[key] = screen_mapping[key]
        else:
            # Fallback: use key itself as screen name if no file mapping found
            screen_dict[key] = _extract_screen_name_from_key(key)
    
    supplementary_dicts.append((screen_dict, 20))  # High weight for screen grouping
    
    # If we have additional processing requirements, we could add more supplementary dicts here
    # For example, if we wanted to group by common patterns or word analysis
    
    # Calculate keys_weight based on wordsToRemove and customMatchFunctions
    # Higher weight means key tokens are preserved over supplementary dict tokens
    keys_weight = 15 if wordsToRemove or customMatchFunctions else 10
    
    # Use compute_nested to create the nested structure
    nested_result = compute_nested(
        unique_keys, 
        *supplementary_dicts,
        keys_weight=keys_weight,
        maxlv=maxlv
    )
    
    # Apply post-processing if wordsToRemove or customMatchFunctions are specified
    if wordsToRemove or customMatchFunctions:
        nested_result = _apply_post_processing(
            nested_result, wordsToRemove, customMatchFunctions, strict_word_splitting
        )
    
    # Flatten the nested structure to get dot notation keys
    flattened = flatten_dict(nested_result)
    
    return flattened


def _extract_screen_name_from_key(key: str) -> str:
    """
    Extract a screen name from a translation key when no file mapping is available.
    
    Args:
        key: Translation key like 'loginButtonLabel'
        
    Returns:
        Inferred screen name like 'loginScreen'
    """
    import re
    
    # Split camelCase and try to identify the main component
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', key)
    
    if not words:
        return key + "Screen"
    
    # Use first significant word as screen identifier
    main_word = words[0].lower()
    return f"{main_word}Screen"


def _apply_post_processing(
    nested_dict: dict,
    wordsToRemove: list = None,
    customMatchFunctions: list = None,
    strict_word_splitting: bool = True
) -> dict:
    """
    Apply post-processing transformations to the nested dictionary keys.
    
    Args:
        nested_dict: Nested dictionary from compute_nested
        wordsToRemove: List of words to remove from keys
        customMatchFunctions: List of transformation functions
        strict_word_splitting: Word splitting mode
        
    Returns:
        Post-processed nested dictionary
    """
    if not wordsToRemove and not customMatchFunctions:
        return nested_dict
    
    def _process_dict(d: dict, level: int = 0) -> dict:
        result = {}
        for key, value in d.items():
            processed_key = key
            
            # Apply word removal (similar to _remove_redundant_words)
            if wordsToRemove and level > 0:  # Don't process top-level keys (screen names)
                processed_key = _remove_words_from_key(processed_key, wordsToRemove, strict_word_splitting)
            
            # Apply custom functions
            if customMatchFunctions:
                processed_key = _apply_custom_functions(processed_key, customMatchFunctions)
            
            # Recursively process nested dictionaries
            if isinstance(value, dict):
                result[processed_key] = _process_dict(value, level + 1)
            else:
                result[processed_key] = value
                
        return result
    
    return _process_dict(nested_dict)


def _remove_words_from_key(key: str, wordsToRemove: list, strict_word_splitting: bool = True) -> str:
    """
    Remove specified words from a key, similar to _remove_redundant_words but simpler.
    """
    import re
    
    if not wordsToRemove or not key:
        return key
    
    original_key = key
    result_key = key
    
    for word_to_remove in wordsToRemove:
        if not word_to_remove:
            continue
        # Create pattern to match the word (case insensitive)
        pattern = re.compile(re.escape(word_to_remove), re.IGNORECASE)
        # Only remove if it's not the entire key
        temp_result = pattern.sub("", result_key)
        if temp_result and temp_result != result_key:
            result_key = temp_result
    
    # Clean up the result (remove empty parts, fix capitalization)
    if result_key:
        # Ensure first letter is lowercase for camelCase
        result_key = (
            result_key[0].lower() + result_key[1:]
            if len(result_key) > 1
            else result_key.lower()
        )
    
    # Safety: Never return empty string - always return at least the original key
    final_result = result_key if result_key else original_key
    
    # Additional safety: if result is just numbers or very short, use original
    if len(final_result) <= 2 or final_result.isdigit():
        final_result = original_key
    
    return final_result


def _snake_to_camel_case(snake_str: str) -> str:
    """
    Convert snake_case string to camelCase.

    Args:
        snake_str: String in snake_case format (e.g., "activity_suggestion_screen")

    Returns:
        String in camelCase format (e.g., "activitySuggestionScreen")
    """
    components = snake_str.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


# Legacy helper functions - keeping for reference but no longer used in normalize_to_nested_map
# The functionality has been replaced by compute_nested from nested_dict module

def _create_grouped_keys(
    keys: list,
    screen_name: str,
    maxlv: int,
    wordsToRemove: list = None,
    customMatchFunctions: list = None,
    strict_word_splitting: bool = True,
) -> dict:
    """
    DEPRECATED: Legacy function replaced by compute_nested.
    Create grouped dot notation keys respecting maxlv by finding common patterns.
    """
    # This function is now replaced by the compute_nested approach
    # Keeping for reference but marking as deprecated
    pass


def _find_common_groups(keys: list) -> dict:
    """
    DEPRECATED: Legacy function replaced by compute_nested.
    Identify common middle patterns in translation keys for grouping.
    """
    pass


def _find_common_pattern(keys: list) -> str:
    """
    DEPRECATED: Legacy function replaced by compute_nested.
    Identify the most frequent suffix pattern across translation keys.
    """
    pass


def _simplify_key(key: str, common_pattern: str) -> str:
    """
    DEPRECATED: Legacy function replaced by compute_nested.
    Simplify a translation key by removing common suffix patterns.
    """
    pass


def _remove_redundant_words(
    key: str, higher_level_words: list, wordsToRemove: list = None, strict_word_splitting: bool = True
) -> str:
    """
    DEPRECATED: Legacy function replaced by compute_nested.
    Remove redundant words from translation keys based on hierarchical context.
    """
    pass


def _apply_custom_functions(key: str, customMatchFunctions: list = None) -> str:
    """
    Apply user-defined transformation functions to translation keys.

    Allows for custom processing logic to be applied to keys after standard
    normalization, enabling project-specific transformations and formatting.

    Args:
        key: The translation key to process
        customMatchFunctions: List of callable functions that accept and return strings

    Returns:
        Processed key after applying all custom transformation functions

    Example:
        customMatchFunctions = [
            lambda x: x.replace('Btn', 'Button'),
            lambda x: x.replace('Msg', 'Message')
        ]
        Input: 'loginBtnMsg' -> Output: 'loginButtonMessage'
    """
    if not customMatchFunctions:
        return key

    result = key
    for func in customMatchFunctions:
        if callable(func):
            try:
                result = func(result)
            except Exception:
                # If custom function fails, continue with current result
                pass

    return result


def iter_original_locale_file(
    path: str, prefixHeader: str = "app_"
) -> Generator[str, None, None]:
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".arb") and file.startswith(prefixHeader):
                yield (
                    os.path.join(root, file),
                    file,
                    file[len(prefixHeader) : -len(".arb")],
                )


@cache
def gather_supported_languages(path: str, prefixHeader: str = "app_") -> list[str]:
    """
    Extract supported language codes from Dart localization files.

    Scans a directory for arb files
    """
    supported = {}
    for file_path, file_name, lang_code in iter_original_locale_file(
        path, prefixHeader
    ):
        # Check if it's a reserved word in Dart
        if lang_code in dart.reserved_words:
            supported[lang_code] = f"{lang_code}_{lang_code.upper()}"
        else:
            supported[lang_code] = lang_code

    return supported


class SlangConfigParams(TypedDict, total=False):
    locales: list[str]
    base_locale: str
    fallback_strategy: str
    lazy: bool
    input_directory: str
    output_directory: str
    output_file_name: str
    input_file_pattern: str
    translate_var: str
    enum_name: str
    class_name: str
    translation_class_visibility: str
    generate_flat_map: bool
    timestamp: bool
    key_case: str
    string_interpolation: str
    context_enum_name: str
    interface_name: str
    build_runner: bool


def get_default_slang_yaml_config(
    locales: list[str],
    base_locale: str = "en",
    fallback_strategy: str = "base_locale",
    lazy: bool = True,
    input_directory: str = "assets/i18n",
    output_directory: str = "lib/i18n",
    output_file_name: str = "translations.g.dart",
    input_file_pattern: str = ".json",
    translate_var: str = "t",
    enum_name: str = "AppLocale",
    class_name: str = "Translations",
    translation_class_visibility: str = "public",
    generate_flat_map: bool = False,
    timestamp: bool = True,
    key_case: str = "camel",
    string_interpolation: str = "double_braces",
    context_enum_name: str = "Context",
    interface_name: str = "AppLocaleUtils",
    build_runner: bool = True,
):
    """
    Return the default slang YAML configuration as a dictionary.

    Returns:
    Dictionary containing default slang configuration settings
    """
    return {
        # Base configuration
        "base_locale": base_locale,
        "fallback_strategy": fallback_strategy,
        "lazy": lazy,
        # Input and output directories
        "input_directory": input_directory,
        "output_directory": output_directory,
        "output_file_name": output_file_name,
        "input_file_pattern": input_file_pattern,
        # Class and file naming
        "translate_var": translate_var,
        "enum_name": enum_name,
        "class_name": class_name,
        # Generation settings
        "translation_class_visibility": translation_class_visibility,
        "generate_flat_map": generate_flat_map,
        "timestamp": timestamp,
        # Locale settings
        "locales": locales,
        # Key case convention
        "key_case": key_case,
        # String interpolation settings
        "string_interpolation": string_interpolation,
        # Context and pluralization
        "context_enum_name": context_enum_name,
        "interface_name": interface_name,
        # Build settings
        "build_runner": build_runner,
    }


def create_slang_yml(
    path: str,
    localeFilePrefix: str = "app_",
    **slangConfigs: typing.Unpack[SlangConfigParams],
):
    """
    Create a YAML file for the slang translations.

    Args:
        path: The directory path where the YAML file will be created.
    """
    import yaml

    supported_languages = list(
        gather_supported_languages(path, localeFilePrefix).values()
    )
    with open(os.path.join(path, "slang.yml"), "w") as yaml_file:
        yaml.safe_dump(
            get_default_slang_yaml_config(supported_languages, **slangConfigs),
            yaml_file,
            indent=2,
        )


def convert_to_slang_translations(
    path: str,
    slangConfigs: dict = None,
    localeFilePrefix: str = "app_",
    normalizedDict: dict = None,
    createMissingPlaceholder: bool = False,
):
    """
    Convert Flutter intl ARB files to slang-compatible JSON format.

    Processes existing ARB locale files and converts them to the nested structure
    expected by slang, using the normalized translation key mapping.

    Args:
        path: Directory containing the ARB locale files
        slangConfigs: Slang configuration dictionary (uses defaults if None)
        localeFilePrefix: Prefix for locale files (default: "app_")
        normalizedDict: Dictionary mapping normalized keys to original keys
        createMissingPlaceholder: If True, create empty string placeholders for missing keys (default: False)

    Returns:
        Dictionary mapping locale codes to their converted translation structures
    """
    import json
    import os


    supportedLocales = gather_supported_languages(path, localeFilePrefix)
    if slangConfigs is None:
        slangConfigs = get_default_slang_yaml_config(list(supportedLocales.values()))

    if normalizedDict is None:
        usageData = gather_intl_translation_usage(path)
        normalizedDict = normalize_to_nested_map(usageData)

    # Create reverse mapping from original keys to normalized keys
    original_to_normalized = {v: k for k, v in normalizedDict.items()}

    converted_translations = {}

    for file_path, file_name, lang_code in iter_original_locale_file(
        path, localeFilePrefix
    ):
        # Read the ARB file as JSON


        try:
            with open(file_path, "r", encoding="utf-8") as f:
                arb_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not read {file_path}: {e}")
            continue

        # Create target structure based on slang configs
        target_structure = {}

        # Process each translation key in the ARB file
        for original_key, translation_value in arb_data.items():
            # Skip metadata keys (start with @)
            if original_key.startswith("@"):
                continue

            # Find the normalized key for this original key
            normalized_key = original_to_normalized.get(original_key)

            if normalized_key:
                # Use deep_set to populate the nested structure
                deep_set(
                    target_structure, normalized_key, translation_value, separator="."
                )
            else:
                # Handle unmapped keys - place them at root level with a warning
                print(
                    f"Warning: No normalized mapping found for key '{original_key}' in {lang_code}"
                )
                target_structure[original_key] = translation_value

        # Store the converted structure
        converted_translations[lang_code] = target_structure

        # Create placeholders for missing normalized keys if requested
        if createMissingPlaceholder:
            for normalized_key in normalizedDict.keys():
                # Check if key already exists using path traversal
                keys = normalized_key.split(".")
                current = target_structure
                exists = True
                for key in keys:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        exists = False
                        break
                
                if not exists:
                    deep_set(target_structure, normalized_key, "", separator=".")

        # Write the converted JSON file based on slang config
        output_dir = slangConfigs.get("input_directory", "assets/i18n")
        # Join output directory with the package entry point path
        output_dir = os.path.join(path, output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # Determine output file pattern
        file_pattern = slangConfigs.get("input_file_pattern", ".json")
        if not file_pattern.startswith("."):
            file_pattern = "." + file_pattern

        output_filename = f"{lang_code}{file_pattern}"
        output_path = os.path.join(output_dir, output_filename)

        # Write the converted file
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(target_structure, f, indent=2, ensure_ascii=False)
            print(f"Successfully converted {file_name} -> {output_filename}")
        except IOError as e:
            print(f"Error writing {output_path}: {e}")

    return converted_translations


def _should_remove_import_line(line: str, replaceTranslationTargets: list[str]) -> bool:
    """
    Check if an import line should be removed based on target patterns.
    
    Args:
        line: The import line to check
        replaceTranslationTargets: List of glob patterns for import files to replace
    
    Returns:
        True if the import line should be removed, False otherwise
    """
    import re
    
    if 'import ' not in line:
        return False
    
    # Extract the import path from the Dart import statement
    # Matches: import 'path/to/file.dart'; or import "path/to/file.dart";
    import_match = re.search(r"import\s+['\"]([^'\"]+)['\"]", line.strip())
    if not import_match:
        return False
    
    import_path = import_match.group(1)
    
    # Convert glob patterns to regex patterns and check if import path matches
    for target_pattern in replaceTranslationTargets:
        # Convert glob pattern to regex
        # * becomes [^/]* (match anything except path separators within a segment)
        # ** becomes .* (match anything including path separators)
        regex_pattern = target_pattern.replace('**', '___DOUBLE_STAR___')
        regex_pattern = regex_pattern.replace('*', '[^/]*')
        regex_pattern = regex_pattern.replace('___DOUBLE_STAR___', '.*')
        regex_pattern = f"^{regex_pattern}$"
        
        if re.search(regex_pattern, import_path):
            return True
    
    return False


def update_dart_imports(
    file_content: str,
    output_directory: str,
    output_file_name: str,
    replaceTranslationTargets: list[str]
) -> tuple[str, bool]:
    """
    Update imports in Dart file content by removing old i18n imports and adding slang import.
    
    Args:
        file_content: Original file content
        output_directory: Output directory for slang translations
        output_file_name: Name of the generated slang file (e.g., 'translations.g.dart')
        replaceTranslationTargets: List of glob patterns for import files to replace
    
    Returns:
        Tuple of (updated_content, imports_changed)
    """
    lines = file_content.split('\n')
    new_lines = []
    # stripping lib 
    if output_directory.startswith("lib/"):
        output_directory = output_directory[4:]

    slang_import_line = f"import '{output_directory}/{output_file_name}';"
    slang_import_added = False
    imports_changed = False
    
    # Check if slang import already exists
    slang_import_exists = any(slang_import_line.strip() in line.strip() for line in lines)
    
    for line in lines:
        should_remove_import = _should_remove_import_line(line, replaceTranslationTargets)
        
        if should_remove_import:
            # Remove old i18n import and add slang import if not already added
            if not slang_import_added and not slang_import_exists:
                # Add slang import in place of the first removed import
                new_lines.append(slang_import_line)
                slang_import_added = True
                imports_changed = True
            # Skip the old import line
            continue
        else:
            new_lines.append(line)
    
    # If no old imports were removed but we still need to add slang import
    if not slang_import_added and not slang_import_exists:
        # Find the last import line and add slang import after it
        insert_position = len(new_lines)  # Default to end of file
        
        for i, line in enumerate(new_lines):
            if line.strip().startswith('import '):
                # Found an import line, find the last consecutive import
                j = i
                while j < len(new_lines) and new_lines[j].strip().startswith('import '):
                    j += 1
                insert_position = j
                break
        
        new_lines.insert(insert_position, slang_import_line)
        imports_changed = True
    
    return '\n'.join(new_lines), imports_changed


def replace_translation_patterns(
    file_content: str,
    translation_keys: list[str],
    original_to_normalized: dict,
    dartAppLocalePrefix: str,
    translate_var: str,
    filename: str = ""
) -> tuple[str, int]:
    """
    Replace AppLocalizations translation patterns with slang format.
    
    Args:
        file_content: Original file content
        translation_keys: List of translation keys expected in this file
        original_to_normalized: Mapping from original keys to normalized keys
        dartAppLocalePrefix: Prefix for AppLocalizations (default: "AppLocalizations")
        translate_var: Variable name for translations (e.g., 't')
        filename: Filename for error reporting
    
    Returns:
        Tuple of (updated_content, replacements_count)
    """
    import re
    
    # Pattern to match AppLocalizations usage
    pattern = rf"{dartAppLocalePrefix}\.of\(context\)!\.(\w+)"
    
    # Create a set of translation keys we expect to find in this file
    expected_keys = set(translation_keys)
    file_replacements = 0
    
    # Find all matches and replace them
    def replace_match(match):
        nonlocal file_replacements
        original_key = match.group(1)
        
        # Only process keys that we know are used in this file
        if original_key not in expected_keys:
            return match.group(0)  # Return original match
        
        # Find the normalized key for this original key
        normalized_key = original_to_normalized.get(original_key)
        
        if normalized_key:
            file_replacements += 1
            # Replace with slang format: t.normalizedKey
            return f"{translate_var}.{normalized_key}"
        else:
            # Keep original if no mapping found
            if filename:
                print(f"Warning: No normalized mapping found for key '{original_key}' in {filename}")
            return match.group(0)  # Return original match
    
    # Perform the replacements
    updated_content = re.sub(pattern, replace_match, file_content)
    
    return updated_content, file_replacements


def update_single_dart_file(
    file_path: str,
    full_file_path: str,
    translation_keys: list[str],
    original_to_normalized: dict,
    dartAppLocalePrefix: str,
    translate_var: str,
    output_directory: str,
    output_file_name: str,
    replaceTranslationTargets: list[str],
    update_imports: bool = True,
    replace_translations: bool = True
) -> dict:
    """
    Update a single Dart file with translation and import changes.
    
    Args:
        file_path: Relative file path for reporting
        full_file_path: Absolute file path
        translation_keys: List of translation keys in this file
        original_to_normalized: Mapping from original keys to normalized keys
        dartAppLocalePrefix: Prefix for AppLocalizations
        translate_var: Variable name for translations
        output_directory: Output directory for slang translations
        output_file_name: Name of the generated slang file (e.g., 'translations.g.dart')
        replaceTranslationTargets: List of glob patterns for import files to replace
        update_imports: Whether to update imports (default: True)
        replace_translations: Whether to replace translation patterns (default: True)
    
    Returns:
        Dictionary with file update results
    """
    filename = os.path.basename(file_path)
    result = {
        'filename': filename,
        'replacements_made': 0,
        'imports_changed': False,
        'updated': False,
        'error': None
    }
    
    try:
        # Read the file
        with open(full_file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        updated_content = original_content
        
        # Update imports if enabled
        if update_imports:
            updated_content, imports_changed = update_dart_imports(
                updated_content, output_directory, output_file_name, replaceTranslationTargets
            )
            result['imports_changed'] = imports_changed
        
        # Replace translation patterns if enabled
        if replace_translations:
            updated_content, file_replacements = replace_translation_patterns(
                updated_content, translation_keys, original_to_normalized,
                dartAppLocalePrefix, translate_var, filename
            )
            result['replacements_made'] = file_replacements
        
        # Write back to file if changes were made
        if updated_content != original_content:
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            result['updated'] = True
            
    except (FileNotFoundError, IOError, UnicodeDecodeError) as e:
        result['error'] = str(e)
    
    return result


def update_dart_file_translations(
    path: str,
    referenceDict: dict,
    normalizedDict: dict,
    slangConfigs: dict = {},
    dartAppLocalePrefix: str = "AppLocalizations",
    replaceTranslationTargets: list[str] = ["*/l10n/app_localizations.dart"],
    update_imports: bool = True,
    replace_translations: bool = True,
    verbose: bool = True
):
    """
    Update Dart files to replace AppLocalizations usage with slang format.
    
    Uses the referenceDict (from gather_intl_translation_usage) to know which files 
    contain which translation keys, then updates them based on the normalized mapping.
    Also updates imports by adding slang import and removing old i18n imports.
    
    Args:
        path: Directory containing Dart files to update
        referenceDict: Dictionary from gather_intl_translation_usage mapping file paths to translation keys
        normalizedDict: Dictionary mapping normalized keys to original keys
        slangConfigs: Slang configuration dictionary
        dartAppLocalePrefix: Prefix for AppLocalizations (default: "AppLocalizations")
        replaceTranslationTargets: List of glob patterns for import files to replace
        update_imports: Whether to update imports (default: True)
        replace_translations: Whether to replace translation patterns (default: True)
        verbose: Whether to print progress messages (default: True)
    
    Returns:
        Dictionary with update statistics and any errors encountered
    """
    import os
    
    # Get translate variable from slang config
    translate_var = slangConfigs.get('translate_var', 't')
    output_directory = slangConfigs.get('output_directory', 'lib/i18n')
    output_file_name = slangConfigs.get('output_file_name', 'translations.g.dart')
    
    # Create reverse mapping from original keys to normalized keys
    original_to_normalized = {v: k for k, v in normalizedDict.items()}
    
    update_stats = {
        'files_processed': 0,
        'files_updated': 0,
        'replacements_made': 0,
        'imports_updated': 0,
        'errors': []
    }
    
    # Process only files that we know contain translation keys
    for file_path, translation_keys in referenceDict.items():
        if not translation_keys:
            continue
            
        # Convert relative path to absolute path
        full_file_path = os.path.join(path, file_path) if not os.path.isabs(file_path) else file_path
        
        if not os.path.exists(full_file_path):
            error_msg = f"File not found: {full_file_path}"
            update_stats['errors'].append(error_msg)
            if verbose:
                print(f"Error: {error_msg}")
            continue
            
        update_stats['files_processed'] += 1
        
        # Update the single file
        file_result = update_single_dart_file(
            file_path, full_file_path, translation_keys, original_to_normalized,
            dartAppLocalePrefix, translate_var, output_directory, output_file_name, replaceTranslationTargets,
            update_imports, replace_translations
        )
        
        # Process results
        if file_result['error']:
            error_msg = f"Error processing {file_result['filename']}: {file_result['error']}"
            update_stats['errors'].append(error_msg)
            if verbose:
                print(f"Error: {error_msg}")
            continue
        
        if file_result['updated']:
            update_stats['files_updated'] += 1
            update_stats['replacements_made'] += file_result['replacements_made']
            if file_result['imports_changed']:
                update_stats['imports_updated'] += 1
            
            if verbose:
                changes_desc = []
                if file_result['replacements_made'] > 0:
                    changes_desc.append(f"{file_result['replacements_made']} replacements")
                if file_result['imports_changed']:
                    changes_desc.append("imports updated")
                
                print(f"Updated {file_result['filename']}: {', '.join(changes_desc)}")
    
    if verbose:
        print(f"Update complete: {update_stats['files_updated']}/{update_stats['files_processed']} files updated, {update_stats['replacements_made']} total replacements, {update_stats['imports_updated']} imports updated")
    
    return update_stats


def _mod_lv_clear_cache():
    # clear all cache funcs
    _cache_dart_file_content.cache_clear()
    gather_supported_languages.cache_clear()
