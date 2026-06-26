// ==========================================
// 📊 Habit Tracker Logic Script
// ==========================================

// --- データの読み込みと保存 ---
let habits = [];

function loadHabits() {
    const saved = localStorage.getItem('yuppi_habits');
    if (saved) {
        try {
            habits = JSON.parse(saved);
        } catch (e) {
            console.error('データの読み込みに失敗しました', e);
            habits = [];
        }
    } else {
        habits = [];
    }
}

function saveHabits() {
    localStorage.setItem('yuppi_habits', JSON.stringify(habits));
    updateGlobalProgress();
}

// --- 日付ヘルパー関数 ---
// 直近7日間の日付オブジェクトの配列を返す (6日前 〜 今日)
function getRecentDates() {
    const dates = [];
    const today = new Date();
    const dayNames = ['日', '月', '火', '水', '木', '金', '土'];

    for (let i = 6; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(today.getDate() - i);

        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const dateStr = `${year}-${month}-${day}`;

        dates.push({
            dateStr: dateStr,
            monthDay: `${d.getMonth() + 1}/${d.getDate()}`,
            dayName: i === 0 ? '今日' : dayNames[d.getDay()],
            isToday: i === 0
        });
    }
    return dates;
}

// 今日の日付文字列を取得 (YYYY-MM-DD)
function getTodayStr() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// --- 統計計算 ---
// 現在の継続日数（ストリーク）を計算する
function calculateStreak(history) {
    let streak = 0;
    const today = new Date();
    
    const formatDate = (d) => {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    // 今日チェックされているか
    let formattedToday = formatDate(today);
    let hasToday = !!history[formattedToday];

    // 昨日チェックされているか
    let yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    let formattedYesterday = formatDate(yesterday);
    let hasYesterday = !!history[formattedYesterday];

    // 今日も昨日もチェックされていなければストリークは 0
    if (!hasToday && !hasYesterday) {
        return 0;
    }

    // 開始日を決定 (今日チェックされていれば今日から、そうでなければ昨日から)
    let currentDate = hasToday ? today : yesterday;

    while (true) {
        let dateStr = formatDate(currentDate);
        if (history[dateStr]) {
            streak++;
            // 1日前へ進める
            currentDate.setDate(currentDate.getDate() - 1);
        } else {
            break;
        }
    }

    return streak;
}

// 直近7日間の達成率を計算する
function calculateWeeklyRate(history, recentDates) {
    let completedCount = 0;
    recentDates.forEach(d => {
        if (history[d.dateStr]) {
            completedCount++;
        }
    });
    return Math.round((completedCount / 7) * 100);
}

// --- UIの描画 ---
const habitForm = document.getElementById('habit-form');
const habitInput = document.getElementById('habit-input');
const habitList = document.getElementById('habit-list');
const emptyState = document.getElementById('empty-state');
const summarySection = document.getElementById('summary-section');
const globalProgressBar = document.getElementById('global-progress-bar');
const globalProgressPercentage = document.getElementById('global-progress-percentage');

// 習慣リスト全体の描画
function renderHabits() {
    // 既存の習慣カードをクリア（空の状態要素は残すために一度非表示に）
    const cards = habitList.querySelectorAll('.habit-card');
    cards.forEach(card => card.remove());

    if (habits.length === 0) {
        emptyState.style.display = 'block';
        summarySection.style.display = 'none';
        return;
    }

    emptyState.style.display = 'none';
    summarySection.style.display = 'block';

    const recentDates = getRecentDates();

    habits.forEach(habit => {
        // カードの作成
        const card = document.createElement('div');
        card.className = 'habit-card';
        card.dataset.id = habit.id;

        // ヘッダー部
        const header = document.createElement('div');
        header.className = 'habit-header';
        
        const title = document.createElement('span');
        title.className = 'habit-title';
        title.textContent = habit.name;

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn-delete';
        deleteBtn.innerHTML = '<i class="fa-regular fa-trash-can"></i>';
        deleteBtn.title = '削除';
        deleteBtn.addEventListener('click', () => deleteHabit(habit.id));

        header.appendChild(title);
        header.appendChild(deleteBtn);
        card.appendChild(header);

        // 過去7日間のグリッド
        const grid = document.createElement('div');
        grid.className = 'history-grid';

        recentDates.forEach(dateInfo => {
            const dayCol = document.createElement('div');
            dayCol.className = 'day-column';

            const dayLabel = document.createElement('span');
            dayLabel.className = 'day-label';
            dayLabel.textContent = dateInfo.dayName;
            if (dateInfo.isToday) {
                dayLabel.style.color = 'var(--primary)';
                dayLabel.style.fontWeight = '700';
            }

            const dateLabel = document.createElement('span');
            dateLabel.className = 'date-label';
            dateLabel.textContent = dateInfo.monthDay;

            const checkBtn = document.createElement('button');
            checkBtn.className = 'btn-check';
            if (habit.history[dateInfo.dateStr]) {
                checkBtn.classList.add('completed');
            }
            checkBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
            checkBtn.title = `${dateInfo.monthDay} の達成状態を切り替え`;

            // クリック時のトグル処理
            checkBtn.addEventListener('click', () => {
                toggleHabit(habit.id, dateInfo.dateStr);
            });

            dayCol.appendChild(dayLabel);
            dayCol.appendChild(dateLabel);
            dayCol.appendChild(checkBtn);
            grid.appendChild(dayCol);
        });
        card.appendChild(grid);

        // 統計情報
        const stats = document.createElement('div');
        stats.className = 'habit-stats';

        const streak = calculateStreak(habit.history);
        const streakInfo = document.createElement('div');
        streakInfo.className = 'streak-info';
        streakInfo.innerHTML = `
            <i class="fa-solid fa-fire"></i>
            <span>連続 <span class="streak-count">${streak}</span> 日</span>
        `;

        const weeklyRate = calculateWeeklyRate(habit.history, recentDates);
        const weeklyInfo = document.createElement('div');
        weeklyInfo.className = 'weekly-rate';
        weeklyInfo.innerHTML = `
            直近7日の達成率: <span class="rate-value">${weeklyRate}%</span>
        `;

        stats.appendChild(streakInfo);
        stats.appendChild(weeklyInfo);
        card.appendChild(stats);

        // コンテナへ追加
        habitList.appendChild(card);
    });

    updateGlobalProgress();
}

// 今日の全体進捗率を更新する
function updateGlobalProgress() {
    if (habits.length === 0) return;

    const todayStr = getTodayStr();
    let completedCount = 0;

    habits.forEach(habit => {
        if (habit.history[todayStr]) {
            completedCount++;
        }
    });

    const progressPercent = Math.round((completedCount / habits.length) * 100);
    globalProgressBar.style.width = `${progressPercent}%`;
    globalProgressPercentage.textContent = `${progressPercent}%`;
}

// --- 習慣の追加・削除・トグル処理 ---

// 追加
function addHabit(name) {
    const cleanName = name.trim();
    if (!cleanName) return;

    const newHabit = {
        id: Date.now().toString(),
        name: cleanName,
        createdAt: getTodayStr(),
        history: {}
    };

    habits.push(newHabit);
    saveHabits();
    renderHabits();
}

// 削除
function deleteHabit(id) {
    if (confirm('この習慣を削除してもよろしいですか？（これまでの記録も消去されます）')) {
        habits = habits.filter(h => h.id !== id);
        saveHabits();
        renderHabits();
    }
}

// チェックの切り替え
function toggleHabit(habitId, dateStr) {
    const habit = habits.find(h => h.id === habitId);
    if (!habit) return;

    if (habit.history[dateStr]) {
        delete habit.history[dateStr];
    } else {
        habit.history[dateStr] = true;
    }

    saveHabits();
    renderHabits();
}

// --- イベントリスナー ---
habitForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = habitInput.value;
    addHabit(name);
    habitInput.value = '';
});

// --- 初期化 ---
document.addEventListener('DOMContentLoaded', () => {
    loadHabits();
    renderHabits();
});
