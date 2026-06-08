# Global Agent Rules

## Core Behaviors & Persona
- Be direct, concise, and professional.
- Avoid writing long conversational fluff (e.g., "Sure, I can help you with that!").
- Do not use placeholders in code; always write fully functional examples.

## Code Style & Tech Stack Preferences
- **Language:** Default to Python (Python 3.12.13) for backend/logic, and use Dash for web development and UI.
- **Styling:** Use Vanilla CSS (custom properties/variables) instead of frameworks unless otherwise requested. Strictly follow the project's exact CSS functions and style patterns.
- **Formatting:** Keep indentation at 2 spaces. Consolidate Python imports at the top of the file in accordance with PEP 8 standards; avoid redundant or local/inline imports.
- **Comments:** Keep comments focused on *why* something is done, not *what* the code does.

## Architecture & Code Organization
- **Separation of Concerns:** Maintain a strict separation between UI layout definitions (in `src/view/pages/`) and callback logic/data handling (centralized in `src/view/view.py`).
- **Utility Functions:** Shared helper and utility functions must be defined in `src/logic/utils.py` rather than nested within business logic or duplicated in UI code.
- **Internationalization (i18n):** Keep translation keys as pure text content, entirely independent of presentation or formatting quirks (like leading/trailing whitespace or newlines). Strip formatting characters from keys and apply them outside the `translate()` calls. Use the module-level dictionary `_translations` for caching, and ensure fallbacks exist for missing locales or keys.

## Design System & Styling
- **Grid System:** The project strictly follows an 8pt Grid System for CSS layout. Standardize margins and paddings using multiples of 8px (e.g., 16px, 24px) to ensure consistent spacing and rhythm across the UI.
- **Theme Palette (UnB Theme):** Use the established color guidelines:
  - `UNB_BLUE`: `'#003366'`
  - `UNB_GREEN`: `'#006633'`
  - `UNB_YELLOW_DARK`: `'#997A00'` (Must be used for yellow elements on light backgrounds to ensure readability).
- **Custom CSS:** Keep utilizing existing custom classes. For instance, `.btn-none` should be used to render buttons with `color="none"`, applying `background-color: transparent !important`, `border: none !important`, and `box-shadow: none !important` across all hover/focus/active states.

## Performance Optimization
- **Pandas Iteration:** Replace `pd.DataFrame.iterrows()` with `itertuples(index=False)` and pre-calculated constants for significant performance gains. Use integer-based indexing on the namedtuple results (e.g., `row[col_idx]`) to safely handle column names with special characters or spaces.
- **Fallback Mechanism:** When using `itertuples()`, implement a `try...except (ValueError, IndexError)` fallback to `iterrows()` to ensure robustness against unexpected column structures or missing data.
- **Vectorization:** Replace iterative Python loops and dictionary constructions with direct `pd.DataFrame` initialization and vectorized operations (division, rounding, `fillna`) wherever possible.

## Testing Best Practices
- **Framework:** The project uses the `unittest` framework. Tests are located in `tests/` and run via `python3 -m unittest discover tests`.
- **Mocking Dependencies:** In environments where heavy dependencies are missing, mock modules like `pandas`, `numpy`, `pyomo`, `psutil`, `diskcache`, `requests`, `multiprocess`, `dash`, `dash_bootstrap_components`, `plotly`, `flask`, and `werkzeug` by assigning `MagicMock()` to `sys.modules` entries before discovering tests.
- **Exceptions:** `requests.RequestException` must be specifically mocked as a class to prevent type errors in error-handling blocks.
- **Isolation:** When unit testing the `i18n.py` module, ensure `_translations.clear()` is called in the `setUp` method to maintain test isolation. Use `unittest.mock.patch` to mock `os.path.exists` and `builtins.open` to simulate file loading behavior without creating temporary files.

## Security & Stability
- **Dependency Management:** When updating dependencies, strictly lock only the direct dependencies using strict equality (e.g., `==`), including packages with extras (e.g., `dash[diskcache]==4.0.0`). Avoid adding transitive or indirect dependencies.
- **Network Requests:** All network requests (e.g., using `requests` or `OSRMClient`) must include an explicit `timeout` parameter (e.g., `timeout=30`) to avoid hanging threads and DoS vulnerabilities.
- **Subprocess Execution:** All external commands executed via `subprocess.run` must be passed as a list of arguments with `shell=False` (default) to prevent command injection. Use `shlex.join()` for safe logging.
- **File Security:** When handling file downloads or uploads, use `werkzeug.utils.secure_filename` and validate filenames and extensions to prevent directory traversal attacks.

## Rules & Constraints
- Do not run command lines that delete files without asking for confirmation first.
- Keep terminal commands simple.
