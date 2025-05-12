# cnChemNER: A Dataset for Chinese Chemical Named Entity Recognition

每个 JSON 文件包含 50 篇专利文献。

## 实体分类体系

![image](https://github.com/user-attachments/assets/9b60e8bf-f857-4fec-9d5c-f3fef3d3b2b2)



## 使用说明

- **Label**：对应 `cate2id.txt` 文件中的行数，表示实体类别。
- **start**：实体的起始位置。
- **end**：实体的结束位置（末位+1）。
- **text**：实体名称。

需要注意的是：
- **id** 与 **type** 这两个字段与实体类别无关，它们是标注过程中的标识符，读者不需要关注这两个关键字。
