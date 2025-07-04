# 定时抢券/点击任务 - 青龙脚本

这是一个通用的、可配置的 Python 脚本，用于在青龙面板上定时模拟对特定 URL（例如京东活动的页面）的点击或POST请求。脚本内置两种模式：**常规模式**和**抢券模式**，以适应不同需求。

## 功能特性

- **双模式运行**:
    - **常规模式**: 未配置特定时间时，按顺序为每个账号执行任务，中间有随机延迟，适合日常签到等普通任务。
    - **抢券模式**: 配置了特定时间点后，脚本会自动切换到高精度模式。它会提前启动，休眠至目标时间点的毫秒级别，然后**并发**为所有账号发送请求���极大提高成功率。
- **多账号支持**: 自动从环境变量 `JD_COOKIE` 中读取所有京东账号并依次执行任务。
- **高度可配置**: 通过环境变量轻松配置目标 URL、请求体 (Request Body) 和 User-Agent。
- **自动识别**: 脚本会自动从 `JD_COOKIE` 中提取账号昵称用于日志输出，并从目标 URL 中提取 `Host` 字段。
- **详细日志**: 输出清晰的执行日志，包括每个请求的精确发送和响应时间，方便排查问题。

## 如何使用

### 1. 添加脚本到青龙面板

1.  登录你的青龙面板。
2.  进入 "定时任务" 页面，点击右上角的 "新建任务"。
3.  **名称**: `定时抢券任务` (或任何你喜欢的名字)
4.  **命令**: `task jd_click_task.py`
5.  **定时规则**:
    - **【抢券模式】**: **必须设置为抢券时间点的前一分钟**。例如，如果你的抢券时间是 `10:00:00` 和 `20:00:00`，你应该将定时规则设置为 `59 9,19 * * *`。这会分别在 `09:59:00` 和 `19:59:00` 启动脚本，然后由脚本内部的计时器精准控制到毫秒。
    - **【常规模式】**: 按你的需求设置即可，例如 `30 8 * * *` (每天早上8:30)。
6.  将 `jd_click_task.py` 文件的内容复制到在线编辑框中。
7.  点击 "保存"。

### 2. 配置环境变量

这是最关键的一步。脚本的运行模式和行为完全依赖于这些环境变量。

在青龙面板的 "配置管理" -> "环境变量" 页面，添加以下变量：

| 变���名                   | 必填 | 说明                                                                                                                                                           | 示例 (仅供参考)                                                                                             |
| ------------------------ | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `JD_COOKIE`              | 是   | 你的京东账号 Cookie。如果��有多个账号，请用 `&` 符号或换行符隔开。                                                                                               | `pt_key=...;pt_pin=...;`                                                                                    |
| `JD_CLICK_URL`           | 是   | 【需要抓包获取】你要模拟点击的目标 URL。                                                                                                                       | `https://api.m.jd.com/client.action?functionId=xxxx`                                                        |
| `JD_CLICK_BODY`          | 是   | 【需要抓包获取】发送 POST 请求时附带的数据 (Request Body)。**请将抓到的 Body 内容压缩成一行**。                                                                    | `{"appId":"xxxx","functionId":"xxxx","body":{"taskId":"123","encryptProjectId":"abc","sourceCode":"A0001"}}` |
| `JD_CLICK_TARGET_TIMES`  | 否   | **【抢券模式开关】** 设置一个或多个抢券时间点，格式为 `HH:MM:SS`，用逗号分隔。**一旦设置此变量，脚本将自动进入抢券模式。** 如果不设置，则为常规模式。 | `10:00:00` 或 `10:00:00,20:00:00`                                                                           |
| `JD_CLICK_USER_AGENT`    | 否   | 【可选，建议提供】模拟请求时的 User-Agent。建议使用你自己抓包时获取的 User-Agent，以提高模拟的真实性。                                                              | `jdapp;iPhone;10.0.2;14.3;...`                                                                              |

---

### 3. 如何抓取网络请求 (URL 和 Body)

要获取 `JD_CLICK_URL` 和 `JD_CLICK_BODY`，你需要使用抓包工具。这里以 `HttpCanary` (小黄鸟) 为例，其他工具如 `Fiddler`, `Charles`, `Mitmproxy` 操作类似。

#### 准备工作

-   在你的安卓手机上安装 `HttpCanary` (小黄鸟) App。
-   根据 `HttpCanary` 的指引完成证书的安装和配置，确保可以抓取 HTTPS 流量。

#### 抓包步骤

1.  **开始抓包**:
    -   打开 `HttpCanary`，选择目标应用为 "京东"，点击右下角蓝色小飞机开始。

2.  **执行操作**:
    -   切换到京东 App，进入活动页面，**执行你想要自动化的那个点击操作** (例如，点击 "立即抢购")。

3.  **停止并分析**:
    -   切换回 `HttpCanary`，停止抓包。

4.  **找到关键请求**:
    -   从请求列表中找到目标请求。通常是 `POST` 类型，域名为 `api.m.jd.com`。

5.  **提取信息**:
    -   **URL**: 在 "概览" 中复制完整 URL -> `JD_CLICK_URL`。
    -   **Body**: 在 "请求" -> "Body" 中复制内容，**并压缩成一行** -> `JD_CLICK_BODY`。
    -   **User-Agent**: 在 "请求" -> "Headers" 中复制 `User-Agent` 的值 -> `JD_CLICK_USER_AGENT`。

将这些值填入青龙面板的环境变量中，然后手动运行一次任务，检查日志是否正常，即可完成配置。

## 免责声明

-   本脚本仅用于学习和技术交流，请勿用于非法用途。
-   使用本脚本所造成的任何后果由使用者自行承担。
-   抢券类活动成功率受网络延迟、服务器性能等多种因素影响，本脚本不能保证100%成功。