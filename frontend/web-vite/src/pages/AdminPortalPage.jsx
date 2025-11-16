import React, { useState, useEffect } from 'react';
import { Layout, Menu, Table, Card, Statistic, Row, Col, Input, Select, Button, Space, Tag, Modal, Descriptions, message } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  HomeOutlined,
  ShoppingCartOutlined,
  StarOutlined,
  DollarOutlined,
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  BankOutlined,
} from '@ant-design/icons';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
import { apiClient } from '../lib/api-client';
import { useAuth } from '../contexts/auth-context';
import dayjs from 'dayjs';

const { Header, Content, Sider } = Layout;
const { Search } = Input;

const AdminPortalPage = () => {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [selectedMenu, setSelectedMenu] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [data, setData] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });
  const [filters, setFilters] = useState({});
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    if (selectedMenu === 'dashboard') {
      fetchStats();
    } else {
      fetchData();
    }
  }, [selectedMenu, pagination.page, pagination.pageSize, filters]);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/v1/admin/stats');
      setStats(response.data.data);
    } catch (error) {
      message.error('Failed to fetch statistics');
    } finally {
      setLoading(false);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.pageSize,
        ...filters,
      };
      const endpoint = getEndpointForMenu(selectedMenu);
      const response = await apiClient.get(endpoint, { params });
      setData(response.data.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.data.pagination?.total || 0,
      }));
    } catch (error) {
      message.error(`Failed to fetch ${selectedMenu}`);
    } finally {
      setLoading(false);
    }
  };

  const getEndpointForMenu = (menu) => {
    const endpoints = {
      users: '/v1/admin/users',
      hotels: '/v1/admin/hotels',
      rooms: '/v1/admin/rooms',
      offers: '/v1/admin/offers',
      bookings: '/v1/admin/bookings',
      reviews: '/v1/admin/reviews',
    };
    return endpoints[menu] || '/v1/admin/users';
  };

  const getColumnsForMenu = (menu) => {
    const columns = {
      users: [
        { title: 'Email', dataIndex: 'email', key: 'email' },
        { title: 'Name', key: 'name', render: (_, record) => `${record.first_name} ${record.last_name}` },
        { title: 'Role', dataIndex: 'role', key: 'role', render: (role) => <Tag color={getRoleColor(role)}>{role}</Tag> },
        { title: 'Status', dataIndex: 'status', key: 'status', render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag> },
        { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm') },
        {
          title: 'Actions',
          key: 'actions',
          render: (_, record) => (
            <Space>
              <Button icon={<EyeOutlined />} onClick={() => viewDetails(record)} />
            </Space>
          ),
        },
      ],
      hotels: [
        { title: 'Name', dataIndex: 'name', key: 'name' },
        { title: 'City', dataIndex: 'city', key: 'city' },
        { title: 'Country', dataIndex: 'country', key: 'country' },
        { title: 'Provider', dataIndex: 'provider', key: 'provider', render: (provider) => <Tag>{provider}</Tag> },
        { title: 'Stars', dataIndex: 'stars', key: 'stars', render: (stars) => '⭐'.repeat(stars) },
        { title: 'Rating', dataIndex: 'rating', key: 'rating' },
        {
          title: 'Actions',
          key: 'actions',
          render: (_, record) => (
            <Space>
              <Button icon={<EyeOutlined />} onClick={() => viewDetails(record)} />
            </Space>
          ),
        },
      ],
      rooms: [
        { title: 'Room Type', dataIndex: 'room_type_name', key: 'room_type_name' },
        { title: 'Hotel ID', dataIndex: 'hotel_id', key: 'hotel_id', render: (id) => id?.substring(0, 8) + '...' },
        { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (date) => dayjs(date).format('YYYY-MM-DD') },
        {
          title: 'Actions',
          key: 'actions',
          render: (_, record) => (
            <Space>
              <Button icon={<EyeOutlined />} onClick={() => viewDetails(record)} />
            </Space>
          ),
        },
      ],
      offers: [
        { title: 'Price', dataIndex: 'price', key: 'price', render: (price, record) => `${record.currency} ${price}` },
        { title: 'Check In', dataIndex: 'check_in', key: 'check_in', render: (date) => dayjs(date).format('YYYY-MM-DD') },
        { title: 'Check Out', dataIndex: 'check_out', key: 'check_out', render: (date) => dayjs(date).format('YYYY-MM-DD') },
        { title: 'Provider', dataIndex: 'provider', key: 'provider', render: (provider) => <Tag>{provider}</Tag> },
        { title: 'Availability', dataIndex: 'availability_count', key: 'availability_count' },
        {
          title: 'Actions',
          key: 'actions',
          render: (_, record) => (
            <Space>
              <Button icon={<EyeOutlined />} onClick={() => viewDetails(record)} />
            </Space>
          ),
        },
      ],
      bookings: [
        { title: 'Guest Name', dataIndex: 'guest_name', key: 'guest_name' },
        { title: 'Guest Email', dataIndex: 'guest_email', key: 'guest_email' },
        { title: 'Total Price', dataIndex: 'total_price', key: 'total_price', render: (price, record) => `${record.currency} ${price}` },
        { title: 'Status', dataIndex: 'status', key: 'status', render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag> },
        { title: 'Booked At', dataIndex: 'booked_at', key: 'booked_at', render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm') },
        {
          title: 'Actions',
          key: 'actions',
          render: (_, record) => (
            <Space>
              <Button icon={<EyeOutlined />} onClick={() => viewDetails(record)} />
            </Space>
          ),
        },
      ],
      reviews: [
        { title: 'Rating', dataIndex: 'rating', key: 'rating', render: (rating) => <Tag color="gold">⭐ {rating}</Tag> },
        { title: 'Author', dataIndex: 'author', key: 'author' },
        { title: 'Title', dataIndex: 'title', key: 'title' },
        { title: 'Provider', dataIndex: 'provider', key: 'provider', render: (provider) => <Tag>{provider}</Tag> },
        { title: 'Fetched At', dataIndex: 'fetched_at', key: 'fetched_at', render: (date) => dayjs(date).format('YYYY-MM-DD') },
        {
          title: 'Actions',
          key: 'actions',
          render: (_, record) => (
            <Space>
              <Button icon={<EyeOutlined />} onClick={() => viewDetails(record)} />
            </Space>
          ),
        },
      ],
    };
    return columns[menu] || [];
  };

  const getRoleColor = (role) => {
    const colors = {
      super_admin: 'red',
      tenant_admin: 'orange',
      manager: 'blue',
      user: 'default',
    };
    return colors[role] || 'default';
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'green',
      pending: 'orange',
      suspended: 'red',
      deleted: 'default',
      confirmed: 'green',
      cancelled: 'red',
    };
    return colors[status] || 'default';
  };

  const viewDetails = (item) => {
    setSelectedItem(item);
    setDetailModalVisible(true);
  };

  const handleTableChange = (newPagination) => {
    setPagination(prev => ({
      ...prev,
      page: newPagination.current,
      pageSize: newPagination.pageSize,
    }));
  };

  const handleSearch = (value) => {
    setFilters(prev => ({ ...prev, search: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: 'users', icon: <UserOutlined />, label: 'Users' },
    { key: 'hotels', icon: <BankOutlined />, label: 'Hotels' },
    { key: 'rooms', icon: <HomeOutlined />, label: 'Rooms' },
    { key: 'offers', icon: <DollarOutlined />, label: 'Offers' },
    { key: 'bookings', icon: <ShoppingCartOutlined />, label: 'Bookings' },
    { key: 'reviews', icon: <StarOutlined />, label: 'Reviews' },
  ];

  if (!user || (user.role !== 'super_admin' && user.role !== 'tenant_admin' && user.user_role !== 'super_admin' && user.user_role !== 'tenant_admin')) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h2>
            <p className="text-gray-600">Admin privileges required.</p>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <Layout style={{ minHeight: '100vh', marginTop: '64px' }}>
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          style={{
            overflow: 'auto',
            height: 'calc(100vh - 64px)',
            position: 'fixed',
            left: 0,
            top: 64,
          }}
        >
          <Menu
            theme="dark"
            selectedKeys={[selectedMenu]}
            mode="inline"
            items={menuItems}
            onClick={({ key }) => setSelectedMenu(key)}
          />
        </Sider>
        <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }}>
          <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', minHeight: 280 }}>
            {selectedMenu === 'dashboard' ? (
              <div>
                <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>
                {stats && (
                  <Row gutter={16}>
                    <Col span={6}>
                      <Card>
                        <Statistic title="Total Users" value={stats.users?.total || 0} />
                        <div className="mt-2">
                          <Tag color="green">Active: {stats.users?.active || 0}</Tag>
                          <Tag color="orange">Pending: {stats.users?.pending || 0}</Tag>
                        </div>
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card>
                        <Statistic title="Total Hotels" value={stats.hotels?.total || 0} />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card>
                        <Statistic title="Total Rooms" value={stats.rooms?.total || 0} />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card>
                        <Statistic title="Total Bookings" value={stats.bookings?.total || 0} />
                      </Card>
                    </Col>
                  </Row>
                )}
              </div>
            ) : (
              <div>
                <div className="mb-4 flex justify-between items-center">
                  <h1 className="text-2xl font-bold capitalize">{selectedMenu}</h1>
                  <Space>
                    <Search
                      placeholder={`Search ${selectedMenu}...`}
                      onSearch={handleSearch}
                      style={{ width: 300 }}
                      allowClear
                    />
                    <Button icon={<ReloadOutlined />} onClick={fetchData}>Refresh</Button>
                  </Space>
                </div>
                <Table
                  columns={getColumnsForMenu(selectedMenu)}
                  dataSource={data}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    current: pagination.page,
                    pageSize: pagination.pageSize,
                    total: pagination.total,
                    showSizeChanger: true,
                    showTotal: (total) => `Total ${total} items`,
                  }}
                  onChange={handleTableChange}
                />
              </div>
            )}
          </Content>
        </Layout>
      </Layout>

      <Modal
        title="Details"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedItem && (
          <Descriptions bordered column={2}>
            {Object.entries(selectedItem).map(([key, value]) => {
              if (key === 'id' || value === null || value === undefined) return null;
              let displayValue = value;
              if (typeof value === 'object') {
                displayValue = JSON.stringify(value, null, 2);
              } else if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
                displayValue = dayjs(value).format('YYYY-MM-DD HH:mm:ss');
              }
              return (
                <Descriptions.Item key={key} label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}>
                  {typeof displayValue === 'string' && displayValue.length > 100 ? (
                    <pre className="whitespace-pre-wrap text-xs">{displayValue}</pre>
                  ) : (
                    displayValue
                  )}
                </Descriptions.Item>
              );
            })}
          </Descriptions>
        )}
      </Modal>

      <Footer />
    </div>
  );
};

export default AdminPortalPage;

