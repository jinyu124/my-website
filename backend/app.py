from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # 允许跨域

# 存储对话历史（生产环境建议使用数据库）
conversation_histories = {}

# DeepSeek R1 API 配置
# API 配置常量
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # R1 模型端点
API_KEY = "sk-715341cc2947422497286d5b2f9902fb"  # TODO: 移入环境变量
REQUEST_TIMEOUT = 10  # 秒
MAX_HISTORY_LENGTH = 10  # 保留最近10条对话

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    
    # 获取或初始化对话历史
    history = conversation_histories.get(user_id, [])
    
    # 构建请求体
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-reasoner",  # 修正模型名称
        "messages": history + [{"role": "user", "content": message}],
        "temperature": 0.7,  # 控制生成文本的随机性
        "max_tokens": 500,   # 控制生成文本的最大长度
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        result = response.json()
        
        if response.status_code == 200:
            ai_response = result['choices'][0]['message']['content']
            # 更新对话历史（保留最近 5 轮对话）
            updated_history = history[-8:] + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": ai_response}
            ]
            conversation_histories[user_id] = updated_history
            return jsonify({"response": ai_response})
        else:
            error_msg = str(result.get('error', {}).get('message', 'API 请求失败'))
            app.logger.error(f"API Error: {error_msg} (Status: {response.status_code})")
            return jsonify({"error": error_msg}), 500
            
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request Error: {str(e)}")
        return jsonify({"error": "网络请求异常，请检查API可用性"}), 500
    except ValueError as e:
        app.logger.error(f"Response Parse Error: {str(e)}")
        return jsonify({"error": "响应解析失败"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)