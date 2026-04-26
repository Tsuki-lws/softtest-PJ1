# A任务交接文档

## 1. 工作完成情况

A 负责的测试实现部分已完成，主要包括：

- 搭建测试环境与 H2 测试数据库配置
- 编写 `service` 层单元测试
- 编写 `controller` 层集成测试
- 补充工具类、异常类、启动入口及关键分支测试
- 生成 JaCoCo 覆盖率报告
- 完成全量自动化测试回归

## 2. 测试脚本范围

### 2.1 单元测试

`service` 层单元测试脚本：

- `src/test/java/com/demo/service/impl/UserServiceImplTest.java`
- `src/test/java/com/demo/service/impl/VenueServiceImplTest.java`
- `src/test/java/com/demo/service/impl/NewsServiceImplTest.java`
- `src/test/java/com/demo/service/impl/MessageServiceImplTest.java`
- `src/test/java/com/demo/service/impl/MessageVoServiceImplTest.java`
- `src/test/java/com/demo/service/impl/OrderServiceImplTest.java`
- `src/test/java/com/demo/service/impl/OrderVoServiceImplTest.java`

补充专项单元测试脚本：

- `src/test/java/com/demo/controller/AdminVenueControllerUnitTest.java`
- `src/test/java/com/demo/controller/UserControllerUnitTest.java`
- `src/test/java/com/demo/utils/FileUtilTest.java`
- `src/test/java/com/demo/exception/LoginExceptionTest.java`
- `src/test/java/com/demo/demoApplicationTests.java`

### 2.2 集成测试

`controller` 层集成测试脚本：

- `src/test/java/com/demo/controller/PublicContentControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/UserControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/OrderControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/MessageControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/AdminUserControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/AdminVenueControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/AdminNewsControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/AdminOrderMessageControllerIntegrationTest.java`

其中 6 条边界、鉴权与安全场景用例已分散并入以下集成测试脚本：

- `src/test/java/com/demo/controller/AdminUserControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/PublicContentControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/UserControllerIntegrationTest.java`
- `src/test/java/com/demo/controller/OrderControllerIntegrationTest.java`

公共测试基座：

- `src/test/java/com/demo/controller/AbstractControllerIntegrationTest.java`
- `src/test/java/com/demo/support/TestDataFactory.java`
- `src/test/java/com/demo/support/MainMethodAutoCloseListener.java`

## 3. 运行方式

在项目目录 `SoftwareTestingDemo/SoftwareTestingDemo` 下执行：

```bash
mvn test
```

测试使用 `src/test/resources/application.yml` 中的 H2 内存数据库配置，不依赖本机 MySQL。

## 4. 执行结果

- Maven Surefire 实际执行测试用例数：`153`
- 测试类 / 测试套件数：`20`
- IDE 测试面板显示：`173/173`
- 执行结果：通过 `147`，失败 `4`，错误 `2`，跳过 `0`

## 5. 覆盖率结果

JaCoCo 报告路径：

- `target/site/jacoco/index.html`

当前覆盖率：

- 主测试范围包指令覆盖率：`100%`
- 主测试范围包分支覆盖率：`100%`
- 主测试范围包行覆盖率：`100%`
- 主测试范围包方法覆盖率：`100%`
- JaCoCo 全量 bundle 指令覆盖率：`64.10%`
- JaCoCo 全量 bundle 分支覆盖率：`18.78%`
- JaCoCo 全量 bundle 行覆盖率：`98.53%`
- JaCoCo 全量 bundle 方法覆盖率：`84.43%`

## 6. 测试设计说明

- 单元测试使用 `JUnit 5 + Mockito`，隔离 DAO 依赖，验证 `service` 层业务逻辑。
- 集成测试使用 `Spring Boot Test + MockMvc + H2`，验证 `controller` 层请求处理、页面跳转、会话状态和数据库变更。
- 常规功能集成测试统一在合法用户会话或管理员会话下执行；另外 6 条边界、鉴权与安全场景用例也已分散并入对应 controller 集成测试类中，覆盖未登录、越权、空值、分页边界、非法参数和密码存储等情况。
- 测试用例覆盖正常路径、异常路径、状态流转、登录鉴权、文件上传和关键边界分支。
- 测试数据由 `TestDataFactory` 和 `AbstractControllerIntegrationTest` 统一维护，保证用例可重复执行。

## 7. 交接状态

A 任务中的测试脚本、测试环境和覆盖率报告已完成。后续最终提交时，直接保留当前 `src/test/java`、`src/test/resources`、`pom.xml` 以及生成的 JaCoCo / Surefire 报告即可；助教执行 `mvn test` 时，会看到当前 6 条边界 / 异常场景用例的失败或报错结果，这与现阶段系统实现一致。
