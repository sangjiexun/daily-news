# 安全注意事项

## ⚠️ 重要安全提示

### 1. 不要使用密码
- **GitHub 和 Gitee 的 API 不支持密码认证**
- GitHub 自 2021年8月13日起已禁用密码认证
- 必须使用 **Personal Access Token (PAT)** 进行认证

### 2. Token 管理
- Token 应该存储在 `config.json` 文件中
- **确保 `config.json` 已添加到 `.gitignore`**（已配置）
- **不要将 `config.json` 提交到 Git 仓库**
- 如果 token 泄露，立即在 GitHub/Gitee 设置中撤销并重新生成

### 3. 如何获取 Token

#### GitHub Token 获取步骤：
1. 登录 GitHub
2. 点击右上角头像 → Settings
3. 左侧菜单选择 "Developer settings"
4. 选择 "Personal access tokens" → "Tokens (classic)"
5. 点击 "Generate new token" → "Generate new token (classic)"
6. 设置名称和过期时间
7. 勾选权限：`repo`（完整仓库访问权限）
8. 点击 "Generate token"
9. **复制 token**（只显示一次，请妥善保存）

#### Gitee Token 获取步骤：
1. 登录 Gitee
2. 点击右上角头像 → 设置
3. 左侧菜单选择 "安全设置" → "私人令牌"
4. 点击 "生成新令牌"
5. 设置描述和权限（至少需要 `projects` 权限）
6. 点击 "提交"
7. **复制 token**（只显示一次，请妥善保存）

### 4. 当前配置
当前 `config.json` 中已配置 token，请确保：
- Token 有效且未过期
- Token 有足够的权限（GitHub 需要 `repo` 权限）
- `config.json` 不会被提交到 Git 仓库

### 5. 如果 Token 失效
如果遇到认证错误，请：
1. 检查 token 是否过期
2. 检查 token 权限是否足够
3. 重新生成 token 并更新 `config.json`

