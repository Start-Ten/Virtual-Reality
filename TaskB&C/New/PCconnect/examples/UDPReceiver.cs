using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System;

public class IMUReceiver : MonoBehaviour
{
    [Header("UDP Settings")]
    public int port = 5005;

    [Header("Data Preview")]
    public float roll;
    public float pitch;
    public float yaw;
    public Vector3 acceleration;

    [Header("Axis Correction")]
    // 根据实际情况调整轴向映射
    // Unity 是左手坐标系 (Y向上, Z向前, X向右)
    // 传感器数据通常是右手坐标系，且定义可能不同
    public bool invertRoll = false;
    public bool invertPitch = false;
    public bool invertYaw = false;

    private UdpClient udpClient;
    private Thread receiveThread;
    private bool isRunning = true;
    
    // 线程安全的数据缓存
    private string lastReceivedPacket = "";
    private object dataLock = new object();

    void Start()
    {
        // 启动后台线程接收 UDP 数据
        receiveThread = new Thread(new ThreadStart(ReceiveData));
        receiveThread.IsBackground = true;
        receiveThread.Start();
        Debug.Log($"UDP Receiver started on port {port}");
    }

    void Update()
    {
        // 在主线程中处理数据并更新物体
        string dataToProcess = null;

        lock (dataLock)
        {
            if (!string.IsNullOrEmpty(lastReceivedPacket))
            {
                dataToProcess = lastReceivedPacket;
                lastReceivedPacket = null; // 清空，避免重复处理
            }
        }

        if (dataToProcess != null)
        {
            ParseAndApply(dataToProcess);
        }
    }

    private void ReceiveData()
    {
        try
        {
            udpClient = new UdpClient(port);
            IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, port);

            while (isRunning)
            {
                try
                {
                    // 阻塞式接收
                    byte[] data = udpClient.Receive(ref anyIP);
                    string text = Encoding.UTF8.GetString(data);

                    lock (dataLock)
                    {
                        lastReceivedPacket = text;
                    }
                }
                catch (Exception err)
                {
                    if (isRunning) Debug.LogWarning($"UDP Receive Error: {err.Message}");
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"UDP Init Error: {e.Message}");
        }
    }

    private void ParseAndApply(string csvData)
    {
        try
        {
            // 数据格式: Roll, Pitch, Yaw, Ax, Ay, Az
            string[] parts = csvData.Split(',');
            if (parts.Length >= 3)
            {
                float r = float.Parse(parts[0]);
                float p = float.Parse(parts[1]);
                float y = float.Parse(parts[2]);

                // 更新 Inspector 面板显示的数值
                roll = r;
                pitch = p;
                yaw = y;

                if (parts.Length >= 6)
                {
                    acceleration = new Vector3(
                        float.Parse(parts[3]),
                        float.Parse(parts[4]),
                        float.Parse(parts[5])
                    );
                }

                // --- 核心：应用旋转 ---
                // 注意：这里需要根据实际效果调整轴向对应关系
                // 假设传感器输出的是欧拉角 (度)
                
                float finalX = invertPitch ? -p : p; // 通常 Pitch 对应 X 轴旋转
                float finalY = invertYaw ? -y : y;   // 通常 Yaw 对应 Y 轴旋转
                float finalZ = invertRoll ? -r : r;  // 通常 Roll 对应 Z 轴旋转

                // 设置物体旋转
                transform.rotation = Quaternion.Euler(finalX, finalY, finalZ);
            }
        }
        catch (Exception e)
        {
            Debug.LogWarning($"Parse Error: {e.Message} | Data: {csvData}");
        }
    }

    void OnDestroy()
    {
        isRunning = false;
        if (udpClient != null)
        {
            udpClient.Close();
            udpClient = null;
        }
        if (receiveThread != null && receiveThread.IsAlive)
        {
            receiveThread.Abort();
        }
    }
}
