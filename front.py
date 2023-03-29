import pandas as pd
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import base64
from pathlib import Path
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import yaml
from streamlit_option_menu import option_menu
from datetime import datetime

# API Connetion and setup

api_key = "secret"
api_base_url = "http://127.0.0.1:5000/api/"

headers = {"X-API-KEY": api_key}

def fetch_data(endpoint, params=None):
    api_url = f"http://127.0.0.1:5000/api/{endpoint}"
    response = requests.get(api_url, headers=headers, params=params)
    
    if response.status_code == 200:
        try:
            data = response.json()
            column_names = data['columns']
            data_dicts = data['data']
            return pd.DataFrame(data_dicts, columns=column_names)
        except Exception as e:
            print("Error parsing JSON data:", e)
            return pd.DataFrame()
    else:
        print(f"Error fetching data from API, status code: {response.status_code}, response content: {response.content}")
        return pd.DataFrame()

# PAGE SETUP 

# Function to convert the image to base64

def img_to_base64(img_path: str) -> str:
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# Displaying logo and title
logo = "logo.png"
encoded_logo = img_to_base64(logo)

st.markdown(f"<p style='text-align: center;'><img src='data:image/png;base64,{encoded_logo}' width=200></p>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>H&M Data - Dashboard</h1>", unsafe_allow_html=True)

# #AUTHENTICATOR 

# Login details: Username: pescobar; Password: abc;

#AUTHENTIOCATION PRE LOGIN 

hashed_passwords = stauth.Hasher(['abc', 'def']).generate()

yaml_config = f'''
credentials:
  usernames: 
    pescobar:
      email: pescobar@gmail.com
      name: Pablo Escobar
      password: {hashed_passwords[0]}
    Hala Madrid:
      email: halamadrid@gmail.com
      name: Hala Madrid
      password: {hashed_passwords[1]}
cookie:
  expiry_days: 30
  key: blabla # Must be string
  name: cookie
preauthorized:
  emails:
  - melsby@gmail.com
'''

config = yaml.load(yaml_config, Loader=yaml.SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'main')

# SIDEBAR WELCOME 
    
st.sidebar.header(f"Welcome to your dashboard!: {name}")
authenticator.logout("Logout", "sidebar")
    
    
# FILTERS IN SIDEBAR 

# Convert age data to a list for use in slider
age_df = fetch_data("customers")
if "age" in age_df.columns:
    age_df = age_df["age"].to_list()
else:
    st.error("The 'age' column is missing in the received data. Please check the API response.")


#FINISHED TRYING

# AUTHENTICATION POST LOGIN 

if authentication_status:
    
    #Horizontal tabs menu
    selected = option_menu(
        menu_title=None, #required
        options=["Customers", "Transactions", "Articles"], #required 
        menu_icon="cast", #optional 
        default_index=0, #optional 
        orientation="horizontal"
    )
    
    st.header(f"You have selected {selected}")
    st.sidebar.write("FILTERS")
    
    #TAB WITH CUSTOMERS
    
    if selected == "Customers":
        
        kpi1, kpi2, kpi3  = st.columns(3)
        # Fetch customers data
        customers_df = fetch_data("customers")
        # Display customers table
        st.header("Data of Customers")
        st.write(customers_df)

        print(customers_df)
        
        #CUSTOMERS SIDEBAR

        age_filtered_lst = st.sidebar.slider(
        'Select ages range',
        0, 100, (30, 90))

        # ages
        st.sidebar.write('Range of selected age:', age_filtered_lst)

        # add club member status filter to sidebar
        status_options = ["ACTIVE", "PRE-CREATE", "LEFT CLUB"]
        selected_status = st.sidebar.selectbox("Status of Club Member", status_options)

        # add fashion news frequency filter to sidebar
        freq_options = ["NONE", "Regularly"]
        selected_freq = st.sidebar.selectbox("Frequency of Fashion News", freq_options)

        # Load customer data based on filters
        query_params = {
        "min_age": age_filtered_lst[0],
        "max_age": age_filtered_lst[1],
        "club_member_status": selected_status,
        "fashion_news_frequency": selected_freq
        }
        customers_df = fetch_data("filtered_customers", params=query_params)
        
        #Calculate KPIs for customer
        num_customers = customers_df["customer_id"].nunique()
        avg_age = customers_df["age"].mean()
    
        # Display KPIs
        kpi1.metric(
        label="Number of Unique Customers",
        value=num_customers,
        delta=num_customers,
        )

        kpi2.metric(
        label="Age Average",
        value=round(avg_age, 2),
        delta=-10 + avg_age,
        )
  
        # Group filtered customers data by age
        customers_grouped = customers_df.groupby("age").size().reset_index(name="count")

        # Create a line chart for filtered customers data
        fig_customers = go.Figure(go.Scatter(x=customers_grouped['age'], y=customers_grouped['count'], name='Age', mode='lines+markers', marker=dict(color='blue')))
        fig_customers.update_layout(xaxis_title='Age', yaxis_title='Count')

        # Display the line chart
        st.header("Age Filtering of Customers")
        st.plotly_chart(fig_customers)
        
        #Member status graph
        
        # Fetch all customers data (without filters)
       
        if selected_status == "ACTIVE":
            filtered_customers_df = customers_df[customers_df["club_member_status"] == "ACTIVE"]
        elif selected_status == "PRE-CREATE":
            filtered_customers_df = customers_df[customers_df["club_member_status"] == "PRE-CREATE"]
        elif selected_status == "LEFT CLUB":
            filtered_customers_df = customers_df[customers_df["club_member_status"] == "LEFT CLUB"]
        else:
            filtered_customers_df = customers_df

        # Assuming the age filter range is given by age_filtered_lst
        filtered_customers_df = customers_df[(customers_df["age"] >= age_filtered_lst[0]) & (customers_df["age"] <= age_filtered_lst[1])]

        # Calculate min and max age
        min_age = filtered_customers_df["age"].min()
        max_age = filtered_customers_df["age"].max()

        # Display min and max age using Streamlit metrics
        kpi1, kpi2 = st.columns(2)
        kpi1.metric(label="Minimum Age", value=min_age)
        kpi2.metric(label="Maximum Age", value=max_age)

        # Group filtered customers data by age
        customers_grouped = filtered_customers_df.groupby("age").size().reset_index(name="count")

        # Create a bar chart for filtered customers data
        fig = px.bar(customers_grouped, x='age', y='count', labels={'age': 'Age', 'count': 'Count'}, color='count', color_continuous_scale='Viridis')

        # Display the bar chart
        st.header("Age Distribution of Customers")
        st.plotly_chart(fig)

            
    #TAB WITH TRANSACTIONS
    
    if selected == "Transactions":
        
        
        #SIDEBAR FOR TRANSACTIONS
        
        # Fetch transactions data
        transactions_df = fetch_data("transactions")
        
        
        # Add a price range slider to the sidebar
        min_price = transactions_df["price"].min()
        max_price = transactions_df["price"].max()
        selected_price_range = st.sidebar.slider(
            "Select price range",
            float(min_price), float(max_price), (float(min_price), float(max_price))
        )

        #Filter the transactions_df based on the selected price range:
        filtered_transactions_df = transactions_df[(transactions_df["price"] >= selected_price_range[0]) & (transactions_df["price"] <= selected_price_range[1])]

        # # Update query_params with the selected price range
        #query_params["min_price"] = selected_price_range[0]
        #query_params["max_price"] = selected_price_range[1]
        
        
        #Display KPIs 
        kpi7, kpi8, kpi9 = st.columns(3)
        
        # Display transactions table
        st.header("Transactions Data")
        st.write(filtered_transactions_df)
        
        # Calculate KPI values for transactions
        num_transactions = len(filtered_transactions_df)
        total_revenue = filtered_transactions_df["price"].sum()
        avg_transaction_value = total_revenue / num_transactions

        # Displaying KPIs for transactions
            
        kpi7.metric(
            label="Number of transactions",
            value=num_transactions,
            delta=num_transactions,
        )

        kpi8.metric(
            label="Total revenue",
            value=round(total_revenue, 2),
            delta=round(total_revenue, 2),
        )

        kpi9.metric(
            label="Average transaction value",
            value=round(avg_transaction_value, 2),
            delta=round(avg_transaction_value, 2),
        )
        
        # Group transactions data by day
        filtered_transactions_df['t_dat'] = pd.to_datetime(filtered_transactions_df['t_dat']).dt.date
        transactions_grouped = filtered_transactions_df.groupby("t_dat").agg({"price": ["count", "sum"]}).reset_index()
        transactions_grouped.columns = ["transaction_date", "transaction_count", "total_revenue"]
        
        # Create a box plot of article prices
        fig_price_boxplot = px.box(
            filtered_transactions_df, x="price", color_discrete_sequence=["blue"]
        )
        fig_price_boxplot.update_layout(
            title="Price Distribution of Articles",
            xaxis_title="Price",
        )

        # Display the box plot
        st.header("Price Distribution of Articles")
        st.plotly_chart(fig_price_boxplot)

        # Convert the transaction date to a string format for better x-axis labels
        filtered_transactions_df["t_dat"] = filtered_transactions_df["t_dat"].astype(str)

        # Create a violin plot for transaction price vs. transaction date
        fig_price_vs_date = px.violin(
            filtered_transactions_df, x="t_dat", y="price",
            labels={"t_dat": "Transaction Date", "price": "Transaction Price"}, box=True, points="all", color_discrete_sequence=["orange"]
        )
        fig_price_vs_date.update_layout(
            title="Transaction Price vs. Transaction Date",
            xaxis_title="Transaction Date",
            yaxis_title="Transaction Price"
        )

        # Display the violin plot
        st.header("Transaction Price vs. Transaction Date")
        st.plotly_chart(fig_price_vs_date)

        
            
    #TAB WITH ARTICLES
    
    if selected == "Articles":
        
        
        # Fetch articles data
        articles_df = fetch_data("articles")
        
        
        #SIDEBAR FOR ARTICLES
        
        # Load articles data based on filters
        colour_options = ['Black', 'White', 'Beige', 'Grey', 'Blue', 'Pink', 'Lilac Purple', 'Red', 'Mole', 'Orange', 'Metal', 'Brown', 'Turquoise', 'Yellow', 'Khaki green', 'Green', 'Unknown', 'Yellowish Green', 'Bluish Green']
        selected_colours = st.sidebar.multiselect(
        "Select colours", 
        colour_options, 
        default=colour_options
        )

        group_options = ['Jersey Basic', 'Under, Nightwear', 'Socks and Tights', 'Jersey Fancy', 'Accessories', 'Trousers Denim', 'Outdoor', 'Shoes', 'Swimwear', 'Knitwear', 'Shirts', 'Trousers', 'Dressed', 'Shorts', 'Dresses Ladies', 'Skirts', 'Special Offers', 'Blouses', 'Unknown', 'Woven/Jersey/Knitted mix Baby', 'Dresses/Skirts girls']
        selected_group = st.sidebar.selectbox(
        "Select garment group", 
        group_options,
        index=group_options.index('Jersey Basic')
        )
        
        # Load article data based on filters
        query_params = {
        "perceived_colours": ', '.join([f"'{colour}'" for colour in selected_colours]),
        "garment_group_name": selected_group
        }
        articles_df = fetch_data("filtered_articles", params=query_params)
        
    
        
        kpi10, kpi11, kpi12 = st.columns(3)
        
        #Display articles table
        st.header("Articles Data")
        st.write(articles_df)

         # Fetch articles data
        articles_df = fetch_data("articles")
        st.write("Raw articles data:")  # Debug statement
        st.write(articles_df)           # Debug statement
        
        #Calculating KPIs
        total_products = articles_df["article_id"].nunique()
        # index_group_name = articles_df['index_group_name'].unique()
        # st.write(index_group_name)
        Ladieswear = articles_df[articles_df.index_group_name == 'Ladieswear']
        perc_Ladieswear = (Ladieswear['article_id'].nunique() / total_products) * 100

  
        menswear = articles_df.index_group_name[articles_df.index_group_name == 'Menswear']
        perc_menswear = (menswear.count()/total_products)*100
       
        
        #Displaying KPIS
        kpi10.metric (
        label="Number of unique products",
        value=total_products,
        delta="updated automatically"
        )
        
        kpi11.metric(
                label = "Ladieswearr",
                value = str(round(perc_Ladieswear, 1)) + '%',
                delta = perc_Ladieswear,
            )

        kpi12.metric(
            label = "Menswear",
            value = str(round(perc_menswear, 1)) + '%',
            delta = perc_menswear,
        )
        
        # Group articles data by color
        articles_grouped = articles_df.groupby("perceived_colour_value_name").size().reset_index(name="count")

        # Displaying filtered data
        # Create a pie chart for filtered articles data
        # Group filtered articles data by color
        articles_filtered_grouped = articles_df.groupby("perceived_colour_value_name").size().reset_index(name="count")

        # Create a pie chart for filtered articles data
        fig_articles_filtered = go.Figure(go.Pie(labels=articles_filtered_grouped['perceived_colour_value_name'], 
                                                values=articles_filtered_grouped['count'], 
                                                name='colour',
                                                marker=dict(colors=px.colors.qualitative.Plotly),
                                                textinfo='label+percent',
                                                insidetextorientation='radial'))

        fig_articles_filtered.update_layout(title='Filtered Articles by Colour', title_x=0.5)

        # Display the pie chart
        st.header("Filtered Articles by Colour")
        st.plotly_chart(fig_articles_filtered)

    
    

elif authentication_status == False:
    st.error('Username/password is incorrect')

elif authentication_status == None:
    st.warning('Please enter your username and password')




