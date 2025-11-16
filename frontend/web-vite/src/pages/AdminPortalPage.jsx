import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  const { tab, page: urlPage } = useParams();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  
  // Get menu from URL or default to dashboard
  const getMenuFromUrl = () => {
    if (tab) {
      // Validate tab is a valid menu item
      const validMenus = ['dashboard', 'users', 'hotels', 'rooms', 'offers', 'bookings', 'reviews'];
      return validMenus.includes(tab) ? tab : 'dashboard';
    }
    return 'dashboard';
  };
  
  // Get page from URL or default to 1
  const getPageFromUrl = () => {
    if (urlPage) {
      const pageNum = parseInt(urlPage, 10);
      return isNaN(pageNum) || pageNum < 1 ? 1 : pageNum;
    }
    return 1;
  };
  
  const [selectedMenu, setSelectedMenu] = useState(getMenuFromUrl());
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [data, setData] = useState([]);
  const [pagination, setPagination] = useState({ 
    page: getPageFromUrl(), 
    pageSize: 20, 
    total: 0 
  });
  const [filters, setFilters] = useState({});
  const filtersRef = useRef(filters);
  const [filtersKey, setFiltersKey] = useState(0); // Force re-render when filters change
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  
  // Track if we're updating URL from user action (to prevent infinite loops)
  const isUpdatingFromUserAction = useRef(false);
  
  // Update URL when tab or page changes
  const updateUrl = useCallback((menu, page = 1) => {
    isUpdatingFromUserAction.current = true;
    if (menu === 'dashboard') {
      navigate('/admin-portal', { replace: true });
    } else if (page === 1) {
      navigate(`/admin-portal/${menu}`, { replace: true });
    } else {
      navigate(`/admin-portal/${menu}/page/${page}`, { replace: true });
    }
    // Reset flag after navigation
    setTimeout(() => {
      isUpdatingFromUserAction.current = false;
    }, 100);
  }, [navigate]);
  
  // Sync state with URL params when they change (e.g., browser back/forward)
  useEffect(() => {
    // Only sync from URL if we're not updating from user action
    if (isUpdatingFromUserAction.current) {
      return;
    }
    
    const menuFromUrl = getMenuFromUrl();
    const pageFromUrl = getPageFromUrl();
    
    // Only update if URL params actually changed
    if (menuFromUrl !== selectedMenu) {
      setSelectedMenu(menuFromUrl);
      setPagination(prev => ({ ...prev, page: pageFromUrl }));
      setFilters({});
    } else if (pageFromUrl !== pagination.page) {
      setPagination(prev => ({ ...prev, page: pageFromUrl }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, urlPage]); // Only depend on URL params, not state

  // Keep filtersRef in sync with filters state
  useEffect(() => {
    filtersRef.current = filters;
    setFiltersKey(prev => prev + 1); // Increment to trigger useEffect
  }, [filters]);

  // Update URL when selectedMenu or pagination.page changes (from user actions)
  // This is handled directly in handleTableChange and menu onClick, so we don't need this useEffect
  // It would cause infinite loops if we update URL here

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/v1/admin/stats');
      setStats(response.data.data);
    } catch (error) {
      message.error('Failed to fetch statistics');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchData = useCallback(async (menu, page, pageSize, filterValues) => {
    setLoading(true);
    try {
      const params = {
        page: page,
        page_size: pageSize,
        ...filterValues,
      };
      const endpoint = getEndpointForMenu(menu);
      console.log('fetchData called:', { menu, endpoint, params, requestedPage: page, requestedPageSize: pageSize });
      const response = await apiClient.get(endpoint, { params });
      console.log('fetchData response:', {
        menu,
        itemsCount: response.data?.data?.items?.length || 0,
        total: response.data?.data?.pagination?.total || 0,
        returnedPage: response.data?.data?.pagination?.page,
        returnedPageSize: response.data?.data?.pagination?.page_size,
        requestedPage: page,
        requestedPageSize: pageSize,
        firstItemId: response.data?.data?.items?.[0]?.id
      });
      const newItems = response.data.data.items || [];
      console.log('Setting new data:', { itemCount: newItems.length, firstItem: newItems[0]?.id });
      setData(newItems);
      setPagination(prev => {
        const newPagination = {
          ...prev,
          page: page, // Preserve the requested page
          pageSize: pageSize, // Preserve the requested pageSize
          total: response.data.data.pagination?.total || 0,
        };
        console.log('Setting new pagination:', newPagination);
        return newPagination;
      });
    } catch (error) {
      console.error('fetchData error:', error);
      message.error(`Failed to fetch ${menu}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedMenu === 'dashboard') {
      fetchStats();
    } else {
      // Only fetch on initial load or when menu/filters change, NOT on pagination change
      // Pagination changes are handled directly in handleTableChange
      console.log('useEffect triggering fetchData (initial load or filter change):', {
        selectedMenu,
        page: pagination.page,
        pageSize: pagination.pageSize,
        filters: filtersRef.current,
        filtersKey
      });
      fetchData(selectedMenu, pagination.page, pagination.pageSize, filtersRef.current);
    }
    // Removed pagination.page and pagination.pageSize from dependencies
    // to prevent double-fetching when pagination changes (handled in handleTableChange)
  }, [selectedMenu, filtersKey, fetchStats, fetchData]);

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

  const handleTableChange = (newPagination, tableFilters, sorter) => {
    // Ant Design Table onChange receives (pagination, filters, sorter)
    const newPage = newPagination.current;
    const newPageSize = newPagination.pageSize;
    
    console.log('handleTableChange called:', {
      newPage,
      newPageSize,
      selectedMenu,
      currentPage: pagination.page,
      currentPageSize: pagination.pageSize
    });
    
    // Update pagination state immediately
    setPagination(prev => ({
      ...prev,
      page: newPage,
      pageSize: newPageSize,
    }));
    
    // Update URL (which will trigger useEffect to sync state)
    updateUrl(selectedMenu, newPage);
    
    // Directly fetch data with new pagination (don't wait for useEffect)
    if (selectedMenu !== 'dashboard') {
      console.log('Directly fetching data for page:', newPage, 'pageSize:', newPageSize);
      fetchData(selectedMenu, newPage, newPageSize, filtersRef.current);
    }
  };

  const handleSearch = (value) => {
    const newFilters = { ...filters, search: value };
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 1 }));
    
    // Update URL to page 1
    updateUrl(selectedMenu, 1);
    
    // Directly fetch data with reset pagination (useEffect will also trigger via filtersKey)
    if (selectedMenu !== 'dashboard') {
      fetchData(selectedMenu, 1, pagination.pageSize, newFilters);
    }
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
            onClick={({ key }) => {
              setSelectedMenu(key);
              // Reset pagination when switching tabs
              setPagination(prev => ({ ...prev, page: 1 }));
              // Clear filters when switching tabs
              setFilters({});
              // Update URL (will trigger useEffect to sync)
              updateUrl(key, 1);
            }}
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
                    <Button icon={<ReloadOutlined />} onClick={() => fetchData(selectedMenu, pagination.page, pagination.pageSize, filters)}>Refresh</Button>
                  </Space>
                </div>
                <Table
                  key={`${selectedMenu}-table`}
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

