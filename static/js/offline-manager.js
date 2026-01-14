// static/js/offline-manager.js - STABLE VERSION
class OfflineManager {
    constructor() {
        this.dbName = 'SchoolMS_Stable';
        this.version = 1;
        this.db = null;
        this.deviceId = this.getDeviceId();
        this.initialized = false;
        this.init();
    }

    async init() {
        try {
            await this.openDatabase();
            this.setupNetworkListeners();
            this.initialized = true;
            console.log('🎯 Offline Manager initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize Offline Manager:', error);
        }
    }

    getDeviceId() {
        let deviceId = localStorage.getItem('device_id');
        if (!deviceId) {
            deviceId = 'device_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('device_id', deviceId);
        }
        return deviceId;
    }

    openDatabase() {
        return new Promise((resolve, reject) => {
            // Close any existing connection first
            if (this.db) {
                this.db.close();
            }

            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = (event) => {
                console.error('❌ Database open error:', event.target.error);
                reject(event.target.error);
            };

            request.onsuccess = (event) => {
                this.db = event.target.result;
                
                // Add error handler for database
                this.db.onerror = (event) => {
                    console.error('❌ Database error:', event.target.error);
                };
                
                this.db.onversionchange = (event) => {
                    console.log('🔄 Database version change detected');
                    this.db.close();
                };
                
                console.log('✅ Database opened successfully');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                console.log('🆕 Creating database stores...');
                
                // Create stores only if they don't exist
                const stores = ['teacher_attendances', 'students', 'staffs', 'results'];
                
                stores.forEach(storeName => {
                    if (!db.objectStoreNames.contains(storeName)) {
                        console.log('➕ Creating store:', storeName);
                        const store = db.createObjectStore(storeName, { 
                            keyPath: 'sync_id'
                        });
                        store.createIndex('sync_status', 'sync_status', { unique: false });
                        store.createIndex('last_modified', 'last_modified', { unique: false });
                        console.log('✅ Created store:', storeName);
                    }
                });
            };

            request.onblocked = () => {
                console.warn('⚠️ Database upgrade blocked by other connections');
            };
        });
    }

    // Ensure database is ready before operations
    async ensureDatabaseReady() {
        if (!this.initialized) {
            await this.init();
        }
        
        if (!this.db) {
            throw new Error('Database not available');
        }
        
        return true;
    }

    async saveLocal(model, data) {
        await this.ensureDatabaseReady();
        
        console.log('💾 Saving to:', model, data);
        
        // Validate input
        if (!data || typeof data !== 'object') {
            throw new Error('Data must be an object');
        }

        // Create a clean copy of data
        const finalData = { ...data };
        
        // Ensure sync_id exists as proper UUID
        if (!finalData.sync_id) {
            finalData.sync_id = this.generateUUID();
        }

        // Add metadata
        finalData.sync_status = 'pending';
        finalData.last_modified = new Date().toISOString();
        finalData.device_id = this.deviceId;

        console.log('📦 Final data to save:', finalData);

        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction([model], 'readwrite');
                const store = transaction.objectStore(model);
                
                const request = store.put(finalData);
                
                request.onsuccess = () => {
                    console.log('✅ Saved to', model, 'ID:', finalData.sync_id);
                    resolve(finalData.sync_id);
                };
                
                request.onerror = (event) => {
                    console.error('❌ Save error:', event.target.error);
                    reject(new Error(`Save failed: ${event.target.error.message}`));
                };

                transaction.oncomplete = () => {
                    console.log('💾 Transaction completed for', model);
                };

                transaction.onerror = (event) => {
                    console.error('❌ Transaction error:', event.target.error);
                };

                transaction.onabort = (event) => {
                    console.error('❌ Transaction aborted:', event.target.error);
                };

            } catch (error) {
                console.error('❌ Unexpected error in saveLocal:', error);
                reject(error);
            }
        });
    }

    async getAllLocal(model) {
        await this.ensureDatabaseReady();
        
        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction([model], 'readonly');
                const store = transaction.objectStore(model);
                const request = store.getAll();
                
                request.onsuccess = () => {
                    console.log(`📊 Retrieved ${request.result.length} records from ${model}`);
                    resolve(request.result);
                };
                
                request.onerror = (event) => {
                    console.error('❌ Get all error:', event.target.error);
                    reject(new Error(`Get all failed: ${event.target.error.message}`));
                };

            } catch (error) {
                console.error('❌ Unexpected error in getAllLocal:', error);
                reject(error);
            }
        });
    }

    async getPendingItems() {
        try {
            const allItems = await this.getAllLocal('teacher_attendances');
            const pendingItems = allItems.filter(item => item.sync_status === 'pending');
            console.log(`📋 Found ${pendingItems.length} pending items`);
            return pendingItems;
        } catch (error) {
            console.error('Error getting pending items:', error);
            return [];
        }
    }

    async syncWithServer() {
        try {
            const pendingItems = await this.getPendingItems();
            if (pendingItems.length === 0) {
                console.log('No pending items to sync');
                this.showSyncStatus('No pending items to sync', 'info');
                return;
            }

            console.log('🔄 Syncing', pendingItems.length, 'items...');
            this.showSyncStatus(`Syncing ${pendingItems.length} items...`, 'info');

            const changes = pendingItems.map(item => ({
                model: 'teacher_attendance',
                operation: 'create',
                data: item
            }));

            console.log('📤 Sending changes to server');

            const response = await fetch('/sync/api/sync/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_id: this.deviceId,
                    changes: changes,
                    last_sync: localStorage.getItem('last_sync') || null
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('📥 Server response:', result);
            
            if (result.status === 'success') {
                // Mark processed items as synced
                for (const change of result.processed_changes) {
                    await this.markAsSynced(change.data.sync_id);
                }
                
                localStorage.setItem('last_sync', result.server_time);
                
                console.log('✅ Sync completed');
                this.showSyncStatus(`Synced ${result.processed_changes.length} items!`, 'success');
            } else {
                throw new Error(result.message || 'Sync failed');
            }
            
        } catch (error) {
            console.error('❌ Sync failed:', error);
            this.showSyncStatus('Sync failed: ' + error.message, 'error');
        }
    }

    async markAsSynced(syncId) {
        await this.ensureDatabaseReady();
        
        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction(['teacher_attendances'], 'readwrite');
                const store = transaction.objectStore('teacher_attendances');
                
                const request = store.get(syncId);
                
                request.onsuccess = () => {
                    const item = request.result;
                    if (item) {
                        item.sync_status = 'synced';
                        store.put(item);
                        console.log('✅ Marked as synced:', syncId);
                    }
                    resolve();
                };
                
                request.onerror = () => reject(request.error);
                
            } catch (error) {
                console.error('❌ Error marking as synced:', error);
                reject(error);
            }
        });
    }

    setupNetworkListeners() {
        window.addEventListener('online', () => {
            this.showSyncStatus('🌐 Connection restored - syncing...', 'info');
            setTimeout(() => this.syncWithServer(), 1000); // Small delay
        });

        window.addEventListener('offline', () => {
            this.showSyncStatus('📵 Working offline', 'warning');
        });

        // Auto-sync with longer interval
        setInterval(() => {
            if (navigator.onLine && this.initialized) {
                this.syncWithServer();
            }
        }, 60000); // 60 seconds
    }

    // Generate proper UUID v4
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    showSyncStatus(message, type) {
        // Remove existing notification
        const existing = document.getElementById('sync-notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.id = 'sync-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            z-index: 10000;
            font-family: Arial, sans-serif;
            font-size: 14px;
            background-color: ${this.getNotificationColor(type)};
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 5000);
    }

    getNotificationColor(type) {
        const colors = {
            'success': '#4CAF50',
            'error': '#f44336',
            'warning': '#ff9800',
            'info': '#2196F3'
        };
        return colors[type] || '#2196F3';
    }

    // Emergency reset if needed
    async resetDatabase() {
        if (this.db) {
            this.db.close();
        }
        
        return new Promise((resolve) => {
            const request = indexedDB.deleteDatabase(this.dbName);
            request.onsuccess = () => {
                console.log('🗑️ Database deleted');
                this.db = null;
                this.initialized = false;
                this.init().then(resolve);
            };
            request.onerror = () => {
                console.error('❌ Failed to delete database');
                resolve();
            };
        });
    }
}

// Initialize offline manager
const offlineManager = new OfflineManager();