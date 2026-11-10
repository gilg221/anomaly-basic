Z_THRESHOLD = 2.0  # пороговый коэффициент k для статистического правила k * sigma
                   # УПРАЖНЕНИЕ 1: поменяйте на 1.5, запустите; затем на 3.0, запустите


def generate_pressure_series(student_n: int) -> tuple[list[float], float, float]:
    """Формирует 12-часовой ряд давления P (атм) и возвращает (ряд, P_min, P_max)."""
    p_base = 160.0 + 2.0 * student_n
    step = float((student_n % 4) + 1)
    # УПРАЖНЕНИЕ 2: замените 22.0 на 1000.0 (это 9-й час) и запустите снова —
    # увидите, как гигантская «шпилька» маскирует провал в 4-м часе
    offsets = [0.0, 1.0, -1.0, -18.0, 2.0, 0.0, -2.0, 1.0, 22.0, -1.0, 1.0, 2.0]
    series: list[float] = []
    for k in offsets:
        series.append(round(p_base + k * step, 2))
    p_min = round(p_base - 10.0 * step, 2)
    p_max = round(p_base + 10.0 * step, 2)
    return series, p_min, p_max


def calc_mean(series: list[float]) -> float:
    """Вычисляет среднее арифметическое числового ряда."""
    if not series:
        raise ValueError("Пустой массив данных")
    total = 0.0
    for val in series:
        total += val
    return total / len(series)


def calc_median(series: list[float]) -> float:
    """Вычисляет медиану ряда без изменения исходного списка."""
    n = len(series)
    if n == 0:
        raise ValueError("Пустой массив данных")
    ordered = sorted(series)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def calc_std(series: list[float], mean_val: float) -> float:
    """Вычисляет стандартное отклонение (СКО, sigma) числового ряда."""
    if not series:
        raise ValueError("Пустой массив данных")
    sq_diff_sum = 0.0
    for val in series:
        sq_diff_sum += (val - mean_val) ** 2
    variance = sq_diff_sum / len(series)
    return variance ** 0.5


def calc_range(series: list[float]) -> tuple[float, float, float]:
    """Возвращает (минимум, максимум, размах вариации) за один проход."""
    if not series:
        raise ValueError("Пустой массив данных")
    lo = hi = series[0]
    for val in series[1:]:
        if val < lo:
            lo = val
        if val > hi:
            hi = val
    return lo, hi, round(hi - lo, 2)


def filter_anomalies(
    series: list[float],
    low_bound: float,
    high_bound: float,
) -> tuple[list[float], list[tuple[int, float]]]:
    """Разделяет ряд на очищенный список и список кортежей аномалий (час, значение)."""
    cleaned: list[float] = []
    anomalies: list[tuple[int, float]] = []
    for hour, val in enumerate(series, start=1):
        if low_bound <= val <= high_bound:
            cleaned.append(val)
        else:
            anomalies.append((hour, val))
    return cleaned, anomalies


def iterative_filter(series: list[float], k: float, passes: int = 2):
    """Двухпроходная очистка: после каждого прохода среднее и СКО
    пересчитываются на очищенном ряде и границы обновляются."""
    cleaned = list(series)
    all_anoms: list[tuple[int, float]] = []
    for _ in range(passes):
        mean_val = calc_mean(cleaned)
        std_val = calc_std(cleaned, mean_val)
        if std_val == 0:
            break
        low, high = mean_val - k * std_val, mean_val + k * std_val
        new_cleaned, anoms = filter_anomalies(cleaned, low, high)
        if not anoms:
            break
        all_anoms.extend(anoms)
        cleaned = new_cleaned
    return cleaned, all_anoms




def replace_outliers_with_neighbor_avg(series: list[float],
                                       low: float,
                                       high: float) -> list[float]:
    """УПРАЖНЕНИЕ 5: импутация — замена выброса полусуммой соседних часов.

    Для крайних точек (первый и последний час) используется медиана ряда.
    Длина ряда при этом сохраняется.
    """
    result = list(series)
    med = calc_median(series)
    for i, val in enumerate(result):
        if val < low or val > high:
            if 0 < i < len(result) - 1:
                result[i] = round((result[i - 1] + result[i + 1]) / 2, 2)
            else:
                result[i] = med
    return result


def main() -> None:
    print("ПОИСК АНОМАЛИЙ И ОЧИСТКА РЯДА ЗАБОЙНОГО ДАВЛЕНИЯ (ВАРИАНТ А)")
    print("=" * 68)
    raw_n = input("Введите ваш номер по журналу N: ").strip()
    student_n = int(raw_n) if raw_n.isdigit() and int(raw_n) > 0 else 5

    pressures, tech_min, tech_max = generate_pressure_series(student_n)

    # Статистики сырого («грязного») ряда
    raw_mean = calc_mean(pressures)
    raw_med = calc_median(pressures)
    raw_std = calc_std(pressures, raw_mean)
    raw_min, raw_max, raw_rng = calc_range(pressures)

    # Статистические границы по правилу k * sigma
    stat_low = round(raw_mean - Z_THRESHOLD * raw_std, 2)
    stat_high = round(raw_mean + Z_THRESHOLD * raw_std, 2)

    print(f"\nИсходный ряд (12 ч): {pressures}")
    print(f"Тех. регламент: [{tech_min:.2f}; {tech_max:.2f}] атм")
    print(f"Границы {Z_THRESHOLD:.1f}*sigma: [{stat_low:.2f}; {stat_high:.2f}] атм")

    print("\nДЕТАЛЬНАЯ ТАБЛИЦА КОНТРОЛЯ ИЗМЕРЕНИЙ")
    print("-" * 68)
    print(f"{'Час':<5}{'P, атм':>10}{'Откл. от ср.':>14}{'Z-оценка':>11}"
          f"{'Тех. коридор':>15}{'Статус точки':>13}")
    print("-" * 68)
    for hour, val in enumerate(pressures, start=1):
        diff = val - raw_mean
        z_score = abs(diff) / raw_std if raw_std > 0 else 0.0
        in_tech = "ОК" if tech_min <= val <= tech_max else "НАРУШЕН"
        is_outlier = (val < stat_low or val > stat_high) or (in_tech == "НАРУШЕН")
        status = "ВЫБРОС!" if is_outlier else "Норма"
        print(f"{hour:<5}{val:>10.2f}{diff:>+14.2f}{z_score:>11.2f}"
              f"{in_tech:>15}{status:>13}")

    # УПРАЖНЕНИЕ 3: фильтрация ряда двухпроходной очисткой
    cleaned_series, found_anomalies = iterative_filter(pressures, Z_THRESHOLD)

    # Статистики очищенного ряда
    cln_mean = calc_mean(cleaned_series)
    cln_med = calc_median(cleaned_series)
    cln_std = calc_std(cleaned_series, cln_mean)
    _, _, cln_rng = calc_range(cleaned_series)

    print("\nРЕЗУЛЬТАТ ФИЛЬТРАЦИИ АНОМАЛИЙ")
    print("-" * 68)
    print(f"Обнаружено выбросов: {len(found_anomalies)} шт. -> {found_anomalies}")
    print(f"Очищенный ряд ({len(cleaned_series)} ч): {cleaned_series}")

    print("\nСРАВНЕНИЕ СТАТИСТИК ДО И ПОСЛЕ ОЧИСТКИ")
    print("-" * 68)
    print(f"{'Показатель':<28}{'До очистки':>14}{'После очистки':>16}{'Изменение':>10}")
    print("-" * 68)
    print(f"{'Среднее арифметическое, атм':<28}{raw_mean:>14.2f}{cln_mean:>16.2f}"
          f"{cln_mean - raw_mean:>+10.2f}")
    print(f"{'Медиана ряда, атм':<28}{raw_med:>14.2f}{cln_med:>16.2f}"
          f"{cln_med - raw_med:>+10.2f}")
    print(f"{'Стандартное отклонение, атм':<28}{raw_std:>14.2f}{cln_std:>16.2f}"
          f"{cln_std - raw_std:>+10.2f}")
    print(f"{'Размах вариации R, атм':<28}{raw_rng:>14.2f}{cln_rng:>16.2f}"
          f"{cln_rng - raw_rng:>+10.2f}")

    # УПРАЖНЕНИЕ 5: импутация аномалий вместо удаления
    imputed_series = replace_outliers_with_neighbor_avg(pressures, stat_low, stat_high)
    print("\nУПРАЖНЕНИЕ 5. ИМПУТАЦИЯ ВЫБРОСОВ (длина ряда сохраняется)")
    print("-" * 68)
    print(f"Ряд с замещением ({len(imputed_series)} ч): {imputed_series}")

    # УПРАЖНЕНИЕ 6: доля бракованной телеметрии и вердикт
    anomaly_rate = len(found_anomalies) / len(pressures) * 100
    if anomaly_rate <= 10:
        verdict = "Канал исправен"
    elif anomaly_rate <= 25:
        verdict = "Требуется калибровка датчика"
    else:
        verdict = "Авария телеметрии"
    print("\nУПРАЖНЕНИЕ 6. КАЧЕСТВО КАНАЛА СВЯЗИ")
    print("-" * 68)
    print(f"Доля брака телеметрии: {anomaly_rate:.1f}% "
          f"({len(found_anomalies)} из {len(pressures)}) — {verdict}")

    # УПРАЖНЕНИЕ 4: демонстрация опасности удаления из списка во время цикла
    demo = [180.0, 110.0, 110.0, 186.0]   # два выброса подряд
    stat_low_demo = 130.0
    for val in demo:
        if val < stat_low_demo:
            demo.remove(val)
    print("\nУПРАЖНЕНИЕ 4. ОПАСНОСТЬ .remove() ВО ВРЕМЯ ЦИКЛА")
    print("-" * 68)
    print(f"Список после цикла: {demo}  <- второй выброс 110.0 «перепрыгнут» и остался!")

    # УПРАЖНЕНИЕ 7: защита от вырожденного (константного) ряда
    const_series = [170.0] * 12           # эффект «залипания» датчика
    const_mean = calc_mean(const_series)
    const_std = calc_std(const_series, const_mean)
    const_val = const_series[0]
    const_z = abs(const_val - const_mean) / const_std if const_std > 0 else 0.0
    print("\nУПРАЖНЕНИЕ 7. КОНСТАНТНЫЙ РЯД (ЗАЛИПАНИЕ ДАТЧИКА)")
    print("-" * 68)
    print(f"Ряд: {const_series}")
    print(f"Среднее = {const_mean:.2f}, СКО (sigma) = {const_std:.2f}, IQR = 0.00")
    print(f"Z-оценка точки: {const_z:.2f} — благодаря защите std > 0 нет ZeroDivisionError")


if __name__ == "__main__":
    main()
