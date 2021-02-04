import streamlit as st
import shap
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import warnings


def st_shap(plot, height=None):
    # plot the shap diagram in stramlit
    shap_html = f"<head>{shap.getjs()}</head><body>{plot.html()}</body>"
    components.html(shap_html, height=height)


def plot_shap_global_and_local(shap_plot_type:str, model:object,  X_train, plot_type:str=None, 
                               max_display:int=None, index_of_explain:int=0):
    """plot the global shap diagram

    Args:
        shap_plot_type: str, the type of shap plot [global | local | scatter]
        model: a trained pycaret model
        plot_type (str): the type of plot   
        max_display (int): the max number rows to display
        X_train (pd.DataFrame): the X training dataset
        index_of_explain (int) : the index of explanation of prediction
    """
    explainer, shap_values, sample_values = get_shap_explainer_global_and_local(model, X_train)
    fig, ax = plt.subplots(nrows=1, ncols=1)
    
    if model.__class__.__name__ == "CatBoostRegressor" or model.__class__.__name__ == "RandomForestRegressor":       
        if shap_plot_type == "global":
            if plot_type == "default":
                plot_type=None
            shap.summary_plot(shap_values, X_train, plot_type=plot_type,show=False)
        else:
            st_shap(shap.force_plot(explainer.expected_value, shap_values[index_of_explain,:],
                                    X_train.iloc[index_of_explain,:]))
            
    elif model.__class__.__name__ == "RANSACRegressor" \
        or model.__class__.__name__ == "KernelRidge" \
        or model.__class__.__name__ == "SVR" \
        or model.__class__.__name__ == "MLPRegressor" \
        or model.__class__.__name__ == "KNeighborsRegressor":
            if shap_plot_type == "global":
                if plot_type == "default":
                    plot_type=None
                shap.summary_plot(shap_values, sample_values)
            else:
                st_shap(shap.force_plot(explainer.expected_value, shap_values[index_of_explain],
                                        sample_values.iloc[index_of_explain]))
            
    else:
        if shap_plot_type == "global": 
            if plot_type == 'bar':
                shap.plots.bar(shap_values, max_display=max_display)
            elif plot_type == 'beeswarm':
                shap.plots.beeswarm(shap_values, max_display=max_display)
            else:
                shap.plots.heatmap(shap_values, max_display=max_display)
        elif shap_plot_type == "local":
            shap.plots.waterfall(shap_values[index_of_explain],max_display=max_display,show=False) 

    return st.pyplot(fig)


def get_shap_kernel(estimator:object,X_train):
    """compute the shap value importance for non-tree based model

    Args:
        estimator (a none tree based sklearn estimator): a sklearn non tree based estimator
        x_train ((pd.DataFrame, np.ndarray),): X training data
        x_test ((pd.DataFrame, np.ndarray),): X testing data

    Returns:
        shap plot
    """
    warnings.filterwarnings("ignore")
    # because the kernel explainer for non-tree based model extremly slower
    # so we must use kmeans to extract mainly information from x_train
    # to speed up the calculation
    if X_train.shape[1] > 3:
        x_train_summary = shap.kmeans(X_train,3)
    else:
        x_train_summary = shap.kmeans(X_train,X_train.shape[1])
    explainer = shap.KernelExplainer(estimator.predict,x_train_summary)

    size = len(X_train)
    if size < 50:
        size = size
    elif size * 0.2 > 50:
        size = 50
    else:
        size = int(size * 0.2)
    sample_values = shap.sample(X_train, size)
    shap_values = explainer.shap_values(sample_values, lr_reg='num_features(10)')

    return explainer, shap_values,sample_values
 
 
@st.cache(allow_output_mutation=True)
def get_shap_explainer_global_and_local(model: object, X_train):
    """return the shap explainer object and shap values for
       global and local plot

    Args:
        model (object): a traine pycaret model
        X_train (pd.DataFrame): the X training data
    """
    sample_values = None
    
    if model.__class__.__name__ == "CatBoostRegressor" \
        or model.__class__.__name__ == "RandomForestRegressor": 
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_train)
    elif model.__class__.__name__ == "RANSACRegressor" \
        or model.__class__.__name__ == "KernelRidge" \
        or model.__class__.__name__ == "SVR" \
        or model.__class__.__name__ == "MLPRegressor" \
        or model.__class__.__name__ == "KNeighborsRegressor":
            explainer, shap_values, sample_values = get_shap_kernel(model, X_train)
    else:
        explainer = shap.Explainer(model, X_train)
        shap_values = explainer(X_train)
        
    return explainer, shap_values, sample_values

    